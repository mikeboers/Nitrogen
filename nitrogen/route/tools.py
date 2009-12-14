"""Module containing tools to assist in building of WSGI routers.

This routing system works by tracking the UNrouted part of the request, and
watching how it changes as it passes through various routers.



"""


import re
import collections
from pprint import pprint
import weakref
import unittest

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

class Route(list):
    
    environ_key = 'nitrogen.route'
    
    @classmethod
    def from_environ(cls, environ):
        if cls.environ_key not in environ:
            environ[cls.environ_key] = cls(get_request_path(environ))
        return environ[cls.environ_key]
    
    def __init__(self, unrouted=None):
        if unrouted:
            self.update(unrouted)
    
    def __getattr__(self, name):
        """Proxy attribute requests to the last chunk."""
        return getattr(self[-1], name)
    
    def update(self, unrouted, router=None, data=None):
        """Sets the current unrouted path and add to routing history.
        
        Params:
            unrouted -- The new unrouted path. Must pass validate_path. 
            router -- Whatever is responsible for this change.
            data -- A mapping of data extracted from the route for this chunk.

        """
        validate_path(unrouted)
        self.append(RouteChunk(unrouted, router, data if data is not None else
            {}))

    def simple_diff(self, i):
        """Return the prefix that was removed at step i, or None if it was not
        a simple refix removal.
        
        Examples:
            >>> r = Route('/one/two')
            >>> r.update('/two')
            >>> r.simple_diff(1)
            '/one'
            
            >>> r = Route('/one/two')
            >>> r.update('/three')
            >>> r.simple_diff(1)
        
        """
        if len(self) < 2:
            return None
        before, after = self[-2].unrouted, self[-1].unrouted
        if not before.endswith(after):
            return None
        return before[:-len(after)] if after else before
        

class RouteChunk(collections.Mapping):

    def __init__(self, unrouted, router=None, data=None):
        self.unrouted = unrouted
        self.router = router
        self.data = data if data is not None else {}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __getattr__(self, name):
        return getattr(self.data, name)
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.unrouted == other.unrouted and
            self.router == other.router and
            self.data == other.data)
    
    @property
    def before(self):
        if self.previous is None:
            raise ValueError('first RouteChunk has no previously unrouted')
        return self.previous.unrouted
    
    @property
    def after(self):
        return self.unrouted

    def __repr__(self):
        return '<%s.%s object at 0x%x: %r by %r>' % (__name__,
            self.__class__.__name__, id(self), self.unrouted, self.router)
            

    
    

    def generate(self, unrouted='', extra=None, one=False):
        """Default generator function.

        Requires the output of the router to be a suffix of the input.

        Examples:
            # >>> RouteChunk(RouteChunk(None,'/one/two'), '/two').generate('/new')
            # '/one/new'
            # >>> RouteChunk(RouteChunk(None, '/a/b/c'), '/c').generate('/d')
            # '/a/b/d'
            # >>> RouteChunk(RouteChunk(None, '/base'), '').generate('/unrouted')
            # '/base/unrouted'

        """
        
        data = {}
        if self.data is not None:
            data.update(self.data)
        if extra is not None:
            data.update(extra)
        
        if self.generator:
            unrouted = self.generator(self, data, unrouted)
            validate_path(unrouted)
        else:
            unrouted = self.simple_diff + unrouted

        if not one and not self.is_first and not self.previous.is_first:
            return self.previous.generate(unrouted, data, one)

        return unrouted

    def url_for(self, route_name=None, _use_unrouted=False, **kwargs):
        if route_name is not None:
            kwargs['route_name'] = route_name
        return self.generate(self.unrouted if _use_unrouted else '', kwargs)


def get_request_path(environ):
    """Get the URI as requested from the environment.

    Pulls from REQUEST_URI if it exists, or the concatenation of SCRIPT_NAME
    and PATH_INFO. Running under apache REQUEST_URI should exist and be set
    to whatever the client sent along.

    """

    if 'REQUEST_URI' in environ:
        path = str(URI(environ['REQUEST_URI']).path)
    else:
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
    return path


def validate_path(path):
    """Assert that a given path is a valid path for routing.

    Throws a ValueError if the path is not a valid routing path, ie., the path
    must be absolute, and not have any dot segments.

    Examples:

        >>> validate_path('/one/two')
        >>> validate_path('/one two')
        >>> validate_path('')

        >>> validate_path('relative')
        Traceback (most recent call last):
        ...
        ValueError: path not absolute: 'relative'

        >>> validate_path('/.')
        Traceback (most recent call last):
        ...
        ValueError: path not normalized: '/.'

    """
    if not path:
        return
    if not path.startswith('/'):
        raise ValueError('path not absolute: %r' % path)

    encoded = Path(path)
    normalized = Path(path)
    normalized.remove_dot_segments()
    if str(encoded) != str(normalized):
        raise ValueError('path not normalized: %r' % path)


def get_route(environ):
    """Gets the list of routing history from the environ."""
    return Route.from_environ(environ)





def test_routing_path_setup():

    def app(_environ, start):
        environ.clear()
        environ.update(_environ)

        start('200 OK', [('Content-Type', 'text-plain')])
        yield get_unrouted(environ)

    app = TestApp(app)

    res = app.get('/one/two')
    assert res.body == '/one/two'

    res = app.get('//leading/and/trailing//')
    assert res.body == '//leading/and/trailing//'

    res = app.get('/./one/../start')
    assert res.body == '/start'


def _assert_next_history_step(res, **kwargs):
    environ_key = 'nitrogen.route.test.history.i'
    environ = res.environ
    # Notice that we are skipping the first one here
    i = environ[environ_key] = environ.get(environ_key, 0) + 1
    chunk = get_route(environ)[i]

    data = kwargs.pop('_data', None)

    for k, v in kwargs.items():
        v2 = getattr(chunk, k, None)
        assert v == v2, 'on key %r: %r (expected) != %r (actual)' % (k, v, v2)

    if data is not None:
        assert dict(chunk.data) == data, '%r != %r' % (dict(chunk.data), data)


def test_routing_path_setup():

    def _app(environ, start):

        start('200 OK', [('Content-Type', 'text-plain')])
        route = get_route(environ)
        path = Path(route.unrouted)
        segment = path.pop(0)
        route.update(unrouted=str(path), router=_app)

        yield 'hi'


    app = TestApp(_app)

    res = app.get('/one/two')
    # print get_route(res.environ)
    _assert_next_history_step(res,
            unrouted='/two',
            router=_app), 'history is wrong'
            
            


# def test_generate_from():
# 
#     environ = dict(REQUEST_URI='/a/b/c/d')
#     route = get_route(environ)
#     route.update('/b/c/d', 1)
#     route.update('/c/d', 2)
#     route.update('/d', 3)
#     route.update('', 4)
# 
#     assert route[4].generate() == '/a/b/c/d', route[4].generate()
#     assert route[3].generate() == '/a/b/c'
#     assert route[2].generate() == '/a/b'
#     assert route[1].generate() == '/a'
# 
#     assert route[3].generate('/new') == '/a/b/c/new', route[3].generate('/new')
    
    
    
    
    
     
            
# ===== NEW STUFF UNDER HERE


class NoParent(ValueError):
    pass


class NoName(ValueError):
    pass


class Unroutable(ValueError):
    pass


class RouterBase(object):
    
    def __init__(self):
        self._parents = []
        self._names = []
        self._name_to_child = {}
    
    def __repr__(self):
        return '<%s.%s:%r>' % (__name__, self.__class__.__name__,
            tuple(self.names))
    
    def __hash__(self):
        return id(self)
    
    def register_child(self, child, name=None):
        if hasattr(child, 'register_parent'):
            child.register_parent(self, via_name=name)
        if name is not None and name not in self._name_to_child:
            self._name_to_child[name] = child
    
    def register_parent(self, parent, via_name):
        self._parents.append(weakref.ref(parent))
        if via_name is not None:
            self._names.append(via_name)
    
    @property
    def parents(self):
        return [x for x in (ref() for ref in self._parents) if x is not None]
    
    @property
    def names(self):
        return list(self._names)
    
    def route_step(self, path):
        """Return (child, newpath, data) or None if it can't be routed."""
        raise NotImplementedError()
    
    def route(self, path):
        # print 'RouterBase.route'
        route = Route(path)
        router = self
        while path and hasattr(router, 'route_step'):
            x = router.route_step(path)
            if x is None:
                raise Unroutable(route, router, path)
            child, path, data = x
            route.update(path, router, data)
            router = child
        return route, router, path
    
    def modify_route(self, path):
        raise NotImplementedError


class PrefixRouter(RouterBase):
    
    def __init__(self, **kwargs):
        super(PrefixRouter, self).__init__()
        self.map = {}
        for prefix, app in kwargs.iteritems():
            self.register(None, prefix, app)
    
    def register(self, name, prefix=None, app=None):
        if prefix is None:
            name, prefix = None, name
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        if app:
            self.map[prefix] = app
            self.register_child(app, name=name)
            return app
        def PrefixRouter_register(app):
            self.register(name, prefix, app)
        return PrefixRouter_register
    
    def route_step(self, path):
        for prefix, child in self.map.iteritems():
            if path == prefix or path.startswith(prefix) and path[len(prefix)] == '/':
                return child, path[len(prefix):], {}
    

class TestCase(unittest.TestCase):
    
    def test_main(self):
    
        app1 = object()
        app2 = object()
        app3 = object()
    
        router = PrefixRouter()
        a = PrefixRouter()
        b = PrefixRouter()

        router.register('a', '/a', a)
        router.register('b', 'b', b)
    
        a.register('1', '/1', app1)
        a.register('2', '/2', app2)
        b.register('2', '2', app2)
        b.register('3', '3', app3)
    
        print router
        print a
        print b
        
        route, child, path = router.route('/a/1')
        self.assertEqual(route, [
            RouteChunk('/a/1'),
            RouteChunk('/1', router),
            RouteChunk('', a),
        ])
        self.assertEqual(child, app1)
        self.assertEqual(path, '')
        
        route, child, path = router.route('/b/2/more')
        self.assertEqual(route, [
            RouteChunk('/b/2/more'),
            RouteChunk('/2/more', router),
            RouteChunk('/more', b),
        ])
        self.assertEqual(child, app2)
        self.assertEqual(path, '/more')
        
        try:
            router.route('/a/extra')
            self.fail()
        except Unroutable as e:
            self.assertEqual(e.args, ([
                RouteChunk('/a/extra'),
                RouteChunk('/extra', router)
            ], a, '/extra'))
        
        


























if __name__ == '__main__':
    from .. import test
    test.run()

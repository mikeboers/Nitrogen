"""Module containing tools to assist in building of WSGI routers.

This routing system works by tracking the UNrouted part of the request, and
watching how it changes as it passes through various routers.



"""


import re
import collections
from pprint import pprint
import weakref
import unittest

from webtest import TestApp as WebTester

from ..uri import URI
from ..uri.path import Path, encode, decode
from ..http.status import HttpNotFound

class Route(list):
    
    environ_key = 'nitrogen.route'
    
    @classmethod
    def from_environ(cls, environ):
        if cls.environ_key not in environ:
            environ[cls.environ_key] = cls(get_request_path(environ))
        return environ[cls.environ_key]
    
    def __init__(self, path=None):
        if path:
            self.update(path)
    
    def __getattr__(self, name):
        """Proxy attribute requests to the last chunk."""
        return getattr(self[-1], name)
    
    def update(self, path, router=None, data=None):
        """Sets the current unrouted path and add to routing history.
        
        Params:
            unrouted -- The new unrouted path. Must pass validate_path. 
            router -- Whatever is responsible for this change.
            data -- A mapping of data extracted from the route for this chunk.

        """
        validate_path(path)
        self.append(RouteChunk(path, router, data if data is not None else
            {}))
    
    def url_for(self, **data):
        for i, chunk in enumerate(self):
            if chunk.router is not None:
                return Router.generate(chunk.router, data, self[i:])
        

class RouteChunk(collections.Mapping):

    def __init__(self, path, router=None, data=None):
        self.path = path
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
        return (self.path == other.path and
            self.router == other.router and
            self.data == other.data)

    def __repr__(self):
        return '<%s.%s at 0x%x: %r by %r with %r>' % (__name__,
            self.__class__.__name__, id(self), self.path, self.router,
            dict(self.data))





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



def simple_diff(before, after):
    """Return the prefix that was removed at step i, or None if it was not
    a simple refix removal.
    
    Examples:
        >>> simple_diff('/one/two', '/two')
        '/one'
        
        >>> simple_diff('/one/two', '/three')
    
    """
    if not before.endswith(after):
        return None
    return before[:-len(after)] if after else before



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
        path = Path(route.path)
        segment = path.pop(0)
        route.update(path=str(path), router=_app)

        yield 'hi'


    app = WebTester(_app)

    res = app.get('/one/two')
    # print get_route(res.environ)
    _assert_next_history_step(res,
            path='/two',
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

class Unroutable(ValueError):
    def __str__(self):
        return 'failed on route %r at %r with %r' % self.args


class GenerationError(ValueError):
    def __str__(self):
        return 'stopped generating at %r by %r with %r' % self.args


class Router(object):
    
    def __repr__(self):
        return '<%s.%s at 0x%x>' % (__name__, self.__class__.__name__,
            id(self))
    
    def route_step(self, path):
        """Return (child, newpath, data) or None if it can't be routed."""
        raise NotImplementedError()
    
    def generate_step(self, data):
        raise NotImplementedError()
    
    def modify_path(self, path):
        return path
    
    def route(self, path):
        route = Route(path)
        router = self
        while hasattr(router, 'route_step'):
            x = router.route_step(path)
            if x is None:
                raise Unroutable(route, router, path)
            child, path, data = x
            route.update(path, router, data)
            router = child
        return route, router, path
    
    def __call__(self, environ, start):
        route = Route.from_environ(environ)
        path = route.path
        x = self.route_step(path)
        if x is None:
            raise HttpNotFound('could not route %r with %r' % (path, self))
        child, path, data = x
        route.update(path, self, data)
        return child(environ, start)
    
    @staticmethod
    def generate(node, new_data, route=None):
        path = []
        route_i = -1
        route_data = {}
        apply_route_data = route is not None
        while node is not None and hasattr(node, 'generate_step'):
            route_i += 1
            if apply_route_data and (len(route) <= route_i or
                route[route_i].router is not node):
                apply_route_data = False
            if apply_route_data:
                route_data.update(route[route_i].data)
            data = route_data.copy()
            data.update(new_data)
            x = node.generate_step(data)
            if x is None:
                raise GenerationError(path, node, data)
            segment, node = x
            path.append(segment)
        return ''.join(path)
    
    def url_for(self, **data):
        return Router.generate(self, data)



        






class TestApp(object):
    
    def __init__(self, output=None, start=True):
        self.start = start
        self.output = output
    
    def __call__(self, environ, start):
        if self.start:
            start('200 OK', [('Content-Type', 'text/plain')])
        return [str(self.output)]
    
    def __repr__(self):
        return 'TestApp(%r)' % self.output



















if __name__ == '__main__':
    from .. import test
    test.run()

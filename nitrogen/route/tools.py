"""Module containing tools to assist in building of WSGI routers.

This routing system works by tracking the UNrouted part of the request, and
watching how it changes as it passes through various routers. URI's are then
rebuilt by stepping backwards through the routing history allowing the routers
to transform the unrouted part, usually by adding a prefix.

By only tracking the unrouted, the routers only have information about their
local space, and not much about how they got to where they are.

The routing history is a list of RouteChunk objects with attributes:
    previous -- The previous routing chunk, or none (if it is supposed to be
        the first).
    unrouted -- What the unrouted path was after this routing step.
    router -- Whatever was responsible for this routing step.
    data
    generator -- A optional callable for generateing the unrouted path.

About generators:

"""


import re
import collections
from pprint import pprint

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

ENVIRON_ROUTE_KEY = 'nitrogen.route'


class Route(list):
    
    def __init__(self, environ):
        self.append(RouteChunk(None, get_request_path(environ), None))
    
    def __getattr__(self, name):
        return getattr(self[-1], name)
    
    @property
    def first(self):
        return self[0]
    
    @property
    def last(self):
        return self[-1]
    
    def update(self, unrouted, router, data=None, generator=None):
        """Sets the unrouted path and adds to routing history.

        This function is to be used by routers which are about to redirect
        control to another WSGI app after consuming some of the unrouted requested
        path. It also established a routing history at the same time which is
        used for debugging (visually in the logs) and for constructing slightly
        modified URLs.

        The unrouted path must pass validation by validate_path(unrouted)

        Params:
            environ -- The request environ that is being routed.
            unrouted -- The new unrouted path.
            router -- Whatever is responsible for this change.
            generator -- A callable for generateing the route in reverse. See the
                module docstring for more info.

        """
        validate_path(unrouted)
        self.append(RouteChunk(self[-1], unrouted, router, data, generator))
        return self[-1]
        
        


class RouteChunk(collections.Mapping):

    def __init__(self, previous, unrouted, router=None, data=None, generator=None):
        self.previous = previous
        self.unrouted = unrouted
        self.router = router
        self.data = data
        self.generator = generator
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __getattr__(self, name):
        return getattr(self.data, name)
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
    
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
            
    @property
    def has_simple_diff(self):
        return self.before.endswith(self.after)
    
    @property
    def is_first(self):
        return self.previous is None

    @property
    def simple_diff(self):
        if not self.has_simple_diff:
            raise ValueError('cannot trivially reverse route %r to %r' % (before, after))
        return self.before[:-len(self.after)] if self.after else self.before

    def generate(self, unrouted='', extra=None, one=False):
        """Default generator function.

        Requires the output of the router to be a suffix of the input.

        Examples:
            >>> RouteChunk(RouteChunk(None,'/one/two'), '/two').generate('/new')
            '/one/new'
            >>> RouteChunk(RouteChunk(None, '/a/b/c'), '/c').generate('/d')
            '/a/b/d'
            >>> RouteChunk(RouteChunk(None, '/base'), '').generate('/unrouted')
            '/base/unrouted'

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
    if ENVIRON_ROUTE_KEY not in environ:
        environ[ENVIRON_ROUTE_KEY] = Route(environ)
    return environ[ENVIRON_ROUTE_KEY]


def get_unrouted(environ):
    """Get the thus unrouted portion of the requested URI from the environ."""
    return get_route(environ).unrouted


def get_route_data(environ):
    return get_route(environ).data


def update_route(environ, *args, **kwargs):
    return get_route(environ).update(*args, **kwargs)









def test_generate_from():

    environ = dict(REQUEST_URI='/a/b/c/d')
    route = get_route(environ)
    route.update('/b/c/d', 1)
    route.update('/c/d', 2)
    route.update('/d', 3)
    route.update('', 4)

    assert route[4].generate() == '/a/b/c/d', route[4].generate()
    assert route[3].generate() == '/a/b/c'
    assert route[2].generate() == '/a/b'
    assert route[1].generate() == '/a'

    assert route[3].generate('/new') == '/a/b/c/new', route[3].generate('/new')






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

        path = Path(get_unrouted(environ))
        segment = path.pop(0)
        update_route(environ, str(path), _app)

        yield 'hi'


    app = TestApp(_app)

    res = app.get('/one/two')
    #print get_route(res.environ)
    _assert_next_history_step(res,
            before='/one/two',
            after='/two',
            router=_app), 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

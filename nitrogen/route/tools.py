"""Module containing tools to assist in building of WSGI routers.

This routing system works by tracking the UNrouted part of the request, and
watching how it changes as it passes through various routers. URI's are then
rebuilt by stepping backwards through the routing history allowing the routers
to transform the unrouted part, usually by adding a prefix.

By only tracking the unrouted, the routers only have information about their
local space, and not much about how they got to where they are.

The routing history is a list of RouteHistoryChunk objects with attributes:
    previous -- The previous routing chunk, or none (if it is supposed to be
        the first).
    unrouted -- What the unrouted path was after this routing step.
    router -- Whatever was responsible for this routing step.
    data
    builder -- A optional callable for rebuilding the unrouted path.

About builders:

"""


import re
import collections
from pprint import pprint

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

ENVIRON_ROUTE_KEY = 'nitrogen.route'

class RouteHistoryChunk(object):
    
    def __init__(self, previous, unrouted, router=None, data=None, builder=None):
        self.previous = previous
        self.unrouted = unrouted
        self.router = router
        self.data = data
        self.builder = builder
    
    @property
    def before(self):
        if not self.previous:
            raise ValueError('first RouteHistoryChunk has no previously unrouted')
        return self.previous.unrouted
    
    @property
    def after(self):
        return self.unrouted
    
    def __repr__(self):
        return '<%s.%s object at 0x%x: %r by %r>' % (__name__,
            self.__class__.__name__, id(self), self.unrouted, self.router)
    
    def is_simple_route(self):
        return self.before.endswith(self.after)
        
    def get_routed(self):
        if not self.is_simple_route():
            raise ValueError('cannot trivially reverse route %r to %r' % (before, after))
        return self.before[:-len(self.after)] if self.after else self.before
    
    def rebuild(self, unrouted, one=False):
        """Default builder function.

        Requires the output of the router to be a suffix of the input.

        Examples:
            >>> RouteHistoryChunk(RouteHistoryChunk(None,'/one/two'), '/two').rebuild('/new')
            '/one/new'
            >>> RouteHistoryChunk(RouteHistoryChunk(None, '/a/b/c'), '/c').rebuild('/d')
            '/a/b/d'
            >>> RouteHistoryChunk(RouteHistoryChunk(None, '/base'), '').rebuild('/unrouted')
            '/base/unrouted'

        """
        
        if self.builder:
            unrouted = self.builder(unrouted)
            validate_path(unrouted)
        else:
            unrouted = self.get_routed() + unrouted
        
        if not one and self.previous and self.previous.previous:
            return self.previous.rebuild(unrouted, one=one)
        
        return unrouted
        

    
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
        ValueError: request path is not absolute: 'relative'
        
        >>> validate_path('/.')
        Traceback (most recent call last):
        ...
        ValueError: request path not normalized: '/.'
    
    """
    if not path:
        return
    if not path.startswith('/'):
        raise ValueError('request path is not absolute: %r' % path)
    
    encoded = Path(path)
    normalized = Path(path)
    normalized.remove_dot_segments()
    if str(encoded) != str(normalized):
        raise ValueError('request path not normalized: %r' % path)
   
   
def get_unrouted(environ):
    """Get the thus unrouted portion of the requested URI from the environ."""
    return get_history(environ)[-1].unrouted


def get_history(environ):
    """Gets the list of routing history from the environ."""
    if ENVIRON_ROUTE_KEY not in environ:
        environ[ENVIRON_ROUTE_KEY] = [
            RouteHistoryChunk(None, get_request_path(environ), None)
        ]
    return environ[ENVIRON_ROUTE_KEY]


def get_data(environ):
    return get_history(environ)[-1].data


def set_unrouted(environ, unrouted, router, data=None, builder=None):
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
        builder -- A callable for rebuilding the route in reverse. See the
            module docstring for more info.
    
    """
    
    validate_path(unrouted)
    history = get_history(environ)
    
    previous = history[-1] if history else None
    history.append(RouteHistoryChunk(previous, unrouted, router, data, builder))
    
    return history[-1]



def build_from(environ, router, route=''):
    
    history = get_history(environ)
    for i, chunk in enumerate(history):
        if chunk.router == router:
            break
    else:
        raise ValueError('could not find router in history')
    
    validate_path(route)
    
    # print history[i]
    return history[i].rebuild(route)
    



def test_build_from():
    
    environ = dict(REQUEST_URI='/a/b/c/d')
    history = get_history(environ)
    set_unrouted(environ, '/b/c/d', 1)
    set_unrouted(environ, '/c/d', 2)
    set_unrouted(environ, '/d', 3)
    set_unrouted(environ, '', 4)
    
    assert build_from(environ, 4) == '/a/b/c/d', build_from(environ, 4)
    assert build_from(environ, 3) == '/a/b/c'
    assert build_from(environ, 2) == '/a/b'
    assert build_from(environ, 1) == '/a'
    
    assert build_from(environ, 3, '/new') == '/a/b/c/new', build_from(environ, 3, 'new')
    
    




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
    chunk = get_history(environ)[i]

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
        set_unrouted(environ, str(path), _app)
        
        yield 'hi'
        

    app = TestApp(_app)

    res = app.get('/one/two')
    #print get_history(res.environ)
    _assert_next_history_step(res, 
            before='/one/two',
            after='/two',
            router=_app), 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

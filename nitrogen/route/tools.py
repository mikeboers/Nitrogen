"""Module containing tools to assist in building of WSGI routers.

This routing system works by tracking the UNrouted part of the request, and
watching how it changes as it passes through various routers.

The routing history is a list of named tuples (HistoryChunk) with parts:
    before -- What the unrouted path was before this routing step.
    after -- What the unrouted path was after this routing step.
    router -- Whatever was responsible for this routing step.
    builder -- A optional callable for rebuilding the unrouted path.

About builders:

"""


# Setup path for local evaluation.
# When copying to another file, just change the parameter to be accurate.
if __name__ == '__main__':
    def __local_eval_fix(package):
        global __package__
        import sys
        __package__ = package
        sys.path.insert(0, '/'.join(['..'] * (1 + package.count('.'))))
        __import__(__package__)
    __local_eval_fix('nitrogen.uri')



import re
import collections
from pprint import pprint

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

ENVIRON_ROUTE_KEY = 'nitrogen.route'

class HistoryChunk(object):
    
    def __init__(self, before, after, router=None, data=None, builder=None):
        self.before = before
        self.after = after
        self.router = router
        self.data = data
        self.builder = builder
    
    def is_simple_route(self):
        return self.before.endswith(self.after)
        
    def get_routed(self):
        if self.is_simple_route():
            return self.before[:-len(self.after)] if self.after else self.before
        raise ValueError('cannot trivially reverse route %r to %r' % (before, after))
    
    def rebuild(self, unrouted):
        """Default builder function.

        Requires the output of the router to be a suffix of the input.

        Examples:
            >>> HistoryChunk('/one/two', '/two').rebuild('/new')
            '/one/new'
            >>> HistoryChunk('/a/b/c', '/c').rebuild('/d')
            '/a/b/d'
            >>> HistoryChunk('/base', '').rebuild('/unrouted')
            '/base/unrouted'

        """
        if self.builder:
            return self.builder(unrouted)
        return self.get_routed() + unrouted
        

    
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
    history = get_history(environ)
    if history:
        return history[-1].after
    return get_request_path(environ)


def get_history(environ):
    """Gets the list of routing history from the environ."""
    if ENVIRON_ROUTE_KEY not in environ:
        environ[ENVIRON_ROUTE_KEY] = []
    return environ[ENVIRON_ROUTE_KEY]


def get_route_data(environ):
    history = get_history(environ)
    if history:
        return history[-1].data


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
        args -- Positional args for the builder.
        kwargs -- Keyword args for the builder.    
    
    """
    
    validate_path(unrouted)
    history = get_history(environ)
    
    before = get_unrouted(environ)
    after = unrouted
    history.append(HistoryChunk(before, after, router, data, builder))



def build_from(environ, router, route=''):
    
    history = get_history(environ)
    for i, chunk in enumerate(history):
        if chunk.router == router:
            break
    else:
        raise ValueError('could not find router in history')
    
    validate_path(route)
    for chunk in reversed(history[:i+1]):
        route = chunk.rebuild(route)
        validate_path(route)
    
    return route
    



def test_build_from():
    
    environ = dict(REQUEST_URI='/a/b/c/d')
    history = get_history(environ)
    set_unrouted(environ, '/b/c/d', 1)
    set_unrouted(environ, '/c/d', 2)
    set_unrouted(environ, '/d', 3)
    set_unrouted(environ, '', 4)
    
    # pprint(history)
    assert build_from(environ, 4) == '/a/b/c/d'
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
    environ_key = 'test.history.i'
    environ = res.environ
    i = environ[environ_key] = environ.get(environ_key, -1) + 1
    chunk = get_history(environ)[i]

    data = kwargs.pop('_data', None)

    for k, v in kwargs.items():
        v2 = getattr(chunk, k, None)
        assert v == v2, '%r != %r' % (v, v2)

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
    # print get_history(res.environ)
    _assert_next_history_step(res, 
            before='/one/two',
            after='/two',
            router=_app), 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

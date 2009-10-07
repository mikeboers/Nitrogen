"""Module containing tools to assist in building of WSGI routers.

The routing history is a list of named tuples (HistoryChunk) with parts:
    before -- What the unrouted path was before this routing step.
    after -- What the unrouted path was after this routing step.
    router -- Whatever was responsible for this routing step.
    builder -- A callable (or none) for rebuilding the unrouted path. See
        below for more info.
    args -- Positional args for the builder.
    kwargs -- Keyword args for the builder.

About builders:
    TODO

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

_ENVIRON_UNROUTED_KEY = 'nitrogen.route.unrouted'
_ENVIRON_HISTORY_KEY = 'nitrogen.route.history'

_HistoryChunk = collections.namedtuple('HistoryChunk', 'path unrouted router builder args kwargs'.split())
class HistoryChunk(_HistoryChunk):
    def __new__(cls, path, unrouted, router, builder=None, args=None, kwargs=None):
        return _HistoryChunk.__new__(cls, path, unrouted, router, builder, args or tuple(), kwargs or {})

    
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
    copy = Path(path)
    copy.remove_dot_segments()
    if path != str(copy):
        raise ValueError('request path not normalized: %r' % path)
   
   
def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI from the environ."""
    if _ENVIRON_UNROUTED_KEY not in environ:
        path = get_request_path(environ)
        validate_path(path)
        environ[_ENVIRON_UNROUTED_KEY] = path
    return environ[_ENVIRON_UNROUTED_KEY]


def get_history(environ):
    """Gets the list of routing history from the environ."""
    if _ENVIRON_HISTORY_KEY not in environ:
        environ[_ENVIRON_HISTORY_KEY] = []
    return environ[_ENVIRON_HISTORY_KEY]


def set_unrouted(environ, unrouted, router, builder=None, args=tuple(), kwargs={}):
    """Sets the unrouted path and adds to routing history.
    
    This function is to be used by routers which are about to redirect
    control to another WSGI app after consuing some of the unrouted requested
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
    history.append(HistoryChunk(get_unrouted(environ), unrouted, router, builder, args, kwargs))
    environ[_ENVIRON_UNROUTED_KEY] = unrouted


def default_builder(route, previous_path, previous_unrouted):
    """Default builder function.
    
    Requires the output of the router to be a suffix of the input.
    
    Examples:
        >>> default_builder('/new', '/one/two', '/two')
        '/one/new'
        >>> default_builder('/d', '/a/b/c', '/c')
        '/a/b/d'
        >>> default_builder('/unrouted', '/base', '')
        '/base/unrouted'
    
    """
    if not previous_path.endswith(previous_unrouted):
        raise ValueError('previous result is not suffix of operand: path=%r unrouted=%r' % (previous_path, previous_unrouted))
    diff = previous_path[:-len(previous_unrouted)] if previous_unrouted else previous_path
    return diff + route

def build_from(environ, router, route=''):
    history = get_history(environ)
    for i, chunk in enumerate(history):
        if chunk.router == router:
            break
    else:
        raise ValueError('could not find router in history')
    for chunk in reversed(history[:i+1]):
        if chunk.builder:
            route = chunk.builder(route, *chunk.args, **chunk.kwargs)
        else:
            route = default_builder(route, chunk.path, chunk.unrouted)
    return route
    

def test_build_from():
    
    environ = dict(REQUEST_URI='/a/b/c/d')
    history = get_history(environ)
    set_unrouted(environ, '/b/c/d', 1)
    set_unrouted(environ, '/c/d', 2)
    set_unrouted(environ, '/d', 3)
    set_unrouted(environ, '', 4)
    
    pprint(history)
    assert build_from(environ, 4) == '/a/b/c/d'
    assert build_from(environ, 3) == '/a/b/c'
    assert build_from(environ, 2) == '/a/b'
    assert build_from(environ, 1) == '/a'
    
    
    
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
    assert get_history(res.environ) == [
        HistoryChunk(
            path='/one/two',
            unrouted='/two',
            router=_app,
            builder=None,
            args=(),
            kwargs={})
        ], 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

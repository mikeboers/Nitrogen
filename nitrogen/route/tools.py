"""Module containing tools to assist in building of WSGI routers.

Routing generally works with two values stored in the request environ: a string
representing what remains to be routed, and a list representing the routing
history of the request.

It is up to the routers to behave nicely with these values, and for the apps to
not touch them. I am in no way putting code in place that asserts that these are
used properly. There are three functions (get_unrouted, set_unrouted, and
get_history) to assist in manupulating these critical values.

The unrouted path is simply a string. When initialized it is normlized somewhat
to remove dot segments ('.' and '..'). It is NEVER asserted that the unrouted
path will remain in this state. The path also tends to (although I haven't
proven this) start out absolute (with a prefixed slash). Simpler routes will
tend to maintain this state, but some (the ReRouter) do not do this nessesarily.
Be careful!

The history is a list of named tuples with properties 'unrouted' (what the value
of the unrouted path was when the router returned), 'router' (the router which
submitted this entry), and 'data' (keyword-arguments handed to set_unrouted by
the router).


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

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

_ENVIRON_UNROUTED_KEY = 'nitrogen.route.unrouted'
_ENVIRON_HISTORY_KEY = 'nitrogen.route.history'

HistoryChunk = collections.namedtuple('HistoryChunk', 'before after router unroute args kwargs'.split())

    
def get_requested(environ):
    raise NotImplemented

def validate_unrouted(path):
    """Assert that a given path is a valid unrouted path.
    
    Throws a ValueError if the path is not a valid unrouted path given the
    routing specifications. Ie: the path must be absolute, and not have any
    dot segments.
    
    Examples:
    
        >>> validate_unrouted('/one/two')
        
        >>> validate_unrouted('relative')
        Traceback (most recent call last):
        ...
        ValueError: request path is not absolute: 'relative'
        
        >>> validate_unrouted('/.')
        Traceback (most recent call last):
        ...
        ValueError: request path not normalized: '/.'
    
    """
    if not path.startswith('/'):
        raise ValueError('request path is not absolute: %r' % path)
    copy = Path(path)
    copy.remove_dot_segments()
    if path != str(copy):
        raise ValueError('request path not normalized: %r' % path)
    
def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if _ENVIRON_UNROUTED_KEY not in environ:
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        validate_unrouted(path)
        environ[_ENVIRON_UNROUTED_KEY] = path
    return environ[_ENVIRON_UNROUTED_KEY]

def get_history(environ):
    if _ENVIRON_HISTORY_KEY not in environ:
        environ[_ENVIRON_HISTORY_KEY] = []
    return environ[_ENVIRON_HISTORY_KEY]

def set_unrouted(environ, unrouted, router, unroute=None, args=tuple(), kwargs={}):
    validate_unrouted(unrouted)
    history = get_history(environ)
    history.append(HistoryChunk(get_unrouted(environ), unrouted, router, unroute, args, kwargs))
    environ[_ENVIRON_UNROUTED_KEY] = unrouted



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
            before='/one/two',
            after='/two',
            router=_app,
            unroute=None,
            args=(),
            kwargs={})
        ], 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

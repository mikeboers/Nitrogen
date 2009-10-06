"""Package for easy routing of requests into request handlers (or WSGI apps.)"""


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

from webtest import TestApp

from ..uri import URI
from ..uri.path import Path, encode, decode

_ENVIRON_UNROUTED_KEY = 'nitrogen.route.unrouted'
_ENVIRON_HISTORY_KEY = 'nitrogen.route.history'

def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if _ENVIRON_UNROUTED_KEY not in environ:
        path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        # print 1, path
        path = Path(path)
        path.remove_dot_segments()
        environ[_ENVIRON_UNROUTED_KEY] = str(path)
    return environ[_ENVIRON_UNROUTED_KEY]


def get_history(environ):
    if _ENVIRON_HISTORY_KEY not in environ:
        environ[_ENVIRON_HISTORY_KEY] = []
        set_unrouted(environ, get_unrouted(environ))
    return environ[_ENVIRON_HISTORY_KEY]


def set_unrouted(environ, unrouted, router=None, **kwargs):
    history = get_history(environ)
    history.append((unrouted, router, kwargs))
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
        set_unrouted(environ, str(path), _app, segment=segment)
        
        yield 'hi'
        

    app = TestApp(_app)

    res = app.get('/one/two')
    assert get_history(res.environ) == [
        ('/one/two', None, {}),
        ('/two', _app, {'segment': u'one'})
    ], 'history is wrong'

if __name__ == '__main__':
    from .. import test
    test.run()

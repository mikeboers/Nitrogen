"""WSGI application runners."""


import atexit
import itertools
import logging
import multiprocessing
import os
import threading
from wsgiref.handlers import CGIHandler as _CGIHandler
from wsgiref.simple_server import make_server as _make_server

from flup.server.fcgi import WSGIServer as _FCGIHandler
from flup.server.fcgi_fork import WSGIServer as _FCGIForkHandler

from . import error


log = logging.getLogger(__name__)


class CGIHandler(_CGIHandler):
    
    error_status = error.DEFAULT_ERROR_HTTP_STATUS
    error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    error_body = error.DEFAULT_ERROR_BODY
    
    def __init__(self, app):
        _CGIHandler.__init__(self)
        self.app = app
    
    def run(self):
        self.run(self.app)


def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    
    CGIHandler(app).run()




class FCGIForkHandler(_FCGIForkHandler):
    
    def __init__(self, *args, **kwargs):
        self._setup = kwargs.pop('setup', None)
        self._teardown = kwargs.pop('teardown', None)
        self._pid = os.getpid()
        super(FCGIForkHandler, self).__init__(*args, **kwargs)
        
    def _child(self, *args):
        
        # Update the "current process". The multiprocessing module does this
        # by setting the _current_process of the process module to the current
        # process. We have to fake this.
        proc = multiprocessing.current_process()
        # proc._identity = ()
        # proc._daemonic = False
        proc._name = 'FcgiFork-%d' % os.getpid()
        proc._parent_pid = self._pid
        proc._popen = None
        proc._counter = itertools.count(1)
        proc._children = set()
        # proc._authkey = AuthenticationString(os.urandom(32))
        proc._tempdir = None
        
        # Run the utilities that setup the multiprocessing environment so that
        # managers still work properly.
        multiprocessing.util._finalizer_registry.clear()
        multiprocessing.util._run_after_forkers()
        
        if self._setup:
            self._setup()
        
        ret = super(FCGIForkHandler, self)._child(*args)
        
        if self._teardown:
            self._teardown()
        
        return ret
        
def run_via_fcgi_thread(app, min_spare=1, max_spare=5, max_total=10, **kwargs):
    """Run a web application via a FastCGI interface of a web server.

    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    _FCGIHandler(app, multithreaded=bool(thread), minSpare=min_spare,
        maxSpare=max_spare, maxThreads=max_total, **kwargs).run()


def run_via_fcgi_fork(app, min_spare=1, max_spare=5, max_total=25,
    max_requests=100, setup=None, teardown=None, **kwargs):
    """Run a web application via a FastCGI interface of a web server.

    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    FCGIForkHandler(app, minSpare=min_spare, maxSpare=max_spare,
        maxChildren=max_total, maxRequests=max_requests, setup=setup,
        teardown=teardown, **kwargs).run()

run_via_fcgi = run_via_fcgi_fork


class SocketHandler(object):
    
    def __init__(self, app, host='', port=8000):
        self.app = app
        self.host = host
        self.port = port
    
    def make_server(self):
        return _make_server(self.host, self.port, self.app)
    
    def handle_request(self):
        self.make_server().handle_request()
    
    def run(self):
        self.make_server().serve_forever()


def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    handler = SocketHandler(app, host, port)
    if once:
        handler.handle_request()
    else:
        handler.run()


if __name__ == '__main__':
    
    def app(env, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'Environment dump:\n\n'
        for k, v in sorted(env.items()):
            yield '%s: %r\n' % (k, v)
        yield '\nDONE.\n'
    
    import random
    
    port = random.randrange(8000, 9000)
    print 'Starting on port %d.' % port
    
    run_via_socket(app, port=port, once=True)



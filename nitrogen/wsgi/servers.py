"""WSGI application runners.

The threading FCGI servers from the single library and flup have some memory
leaks. I was able to patch one of the larger ones. This patch also fixes the
prefork server as well. After the memory stablizes, we are now using ~45MB
maxres, instead of ~60MB (after a few thousand... but this one would keep
growing). I actually saw the unpatched one hit 150MB once.

Forking notes:
    - the master proc does not appear to leak memory it all. it is constant at
      around 18M of memory. this is not using a manager
    - a child starts at 2961408
    - by 1000 requests: 3809280
    - by 2000 requests: 3809280
    - it does not go higher


"""


import itertools
import multiprocessing.util
import os
from wsgiref.handlers import CGIHandler as _CGIServer
from wsgiref.simple_server import make_server as _make_server

from flup.server.fcgi_base import Request as _FlupFCGIRequest
from flup.server.fcgi import WSGIServer as _FCGIThreadPoolServer
from flup.server.fcgi_fork import WSGIServer as _FCGIForkServer

from .. import error
from .lib.fcgi import Request as _FCGIRequest, WSGIServer as _FCGIThreadServer


def monkeypatch_fcgi_request(Request):
    """Fixing a memory leak in the fcgi Request classes.
    
    It dels all the data associated with this request. There appears to be a
    number of references cycles involving the request, its input/output,
    environment, ect. Before I did his the process gained 1MB after a couple
    dozen requests. After, it gains less than 1MB over 10k requests.
    
    """
    old_end = Request._end
    def new_end(self, *args):
        old_end(self, *args)
        self.__dict__.clear()
    Request._end = new_end


monkeypatch_fcgi_request(_FCGIRequest)
monkeypatch_fcgi_request(_FlupFCGIRequest)


class CGIServer(_CGIServer):

    error_status = error.DEFAULT_ERROR_HTTP_STATUS
    error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    error_body = error.DEFAULT_ERROR_BODY

    def __init__(self, app):
        _CGIServer.__init__(self)
        self.app = app

    def run(self):
        _CGIServer.run(self, self.app)


class FCGIThreadServer(_FCGIThreadServer):
    """Only purpose of this class is to change the class name."""
    pass


class FCGIThreadPoolServer(_FCGIThreadPoolServer):

    def __init__(self, app, min_spare=1, max_spare=5, max_threads=50):
        super(FCGIThreadPoolServer, self).__init__(app, minSpare=min_spare,
            maxSpare=max_spare, maxThreads=max_threads)


class FCGIForkServer(_FCGIForkServer):

    def __init__(self, app, min_spare=1, max_spare=4, max_children=10,
        max_requests=0, setup=None, teardown=None):

        self._setup_child = setup
        self._teardown_child = teardown
        self._pid = os.getpid()

        super(FCGIForkServer, self).__init__(app, minSpare=min_spare,
            maxSpare=max_spare, maxChildren=max_children,
            maxRequests=max_requests)

    def setup_child(self):
        if self._setup_child:
            self._setup_child()

    def teardown_child(self):
        if self._teardown_child:
            self._teardown_child()

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

        self.setup_child()

        ret = super(FCGIForkServer, self)._child(*args)

        self.teardown_child()

        return ret


class SocketServer(object):

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


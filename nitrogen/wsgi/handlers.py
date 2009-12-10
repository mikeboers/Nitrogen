"""WSGI application runners."""


import itertools
import multiprocessing.util
import os
from wsgiref.handlers import CGIHandler as _CGIHandler
from wsgiref.simple_server import make_server as _make_server

from flup.server.fcgi import WSGIServer as _FCGIThreadPoolHandler
from flup.server.fcgi_fork import WSGIServer as _FCGIForkHandler

from .fcgi import WSGIServer as FCGIThreadHandler
from .. import error


class CGIHandler(_CGIHandler):

    error_status = error.DEFAULT_ERROR_HTTP_STATUS
    error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    error_body = error.DEFAULT_ERROR_BODY

    def __init__(self, app):
        _CGIHandler.__init__(self)
        self.app = app

    def run(self):
        _CGIHandler.run(self, self.app)


class FCGIThreadPoolHandler(_FCGIThreadPoolHandler):

    def __init__(self, app, min_spare=1, max_spare=5, max_threads=50):
        super(FCGIThreadPoolHandler, self).__init__(app, minSpare=min_spare,
            maxSpare=max_spare, maxThreads=max_threads)


class FCGIForkHandler(_FCGIForkHandler):

    def __init__(self, app, min_spare=1, max_spare=5, max_children=50,
        max_requests=0, setup=None, teardown=None):

        self._setup_child = setup
        self._teardown_child = teardown
        self._pid = os.getpid()

        super(FCGIForkHandler, self).__init__(app, minSpare=min_spare,
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

        ret = super(FCGIForkHandler, self)._child(*args)

        self.teardown_child()

        return ret


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

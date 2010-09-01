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
import logging
import multiprocessing.util
import os
import re
import sys
import time

from flup.server.fcgi_base import Request as _FCGIRequest, FCGI_REQUEST_COMPLETE
from flup.server.fcgi import WSGIServer as _FCGIServer
from flup.server.fcgi_fork import WSGIServer as _FCGIPreForkServer

from .. import status


log = logging.getLogger(__name__)


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






log = logging.getLogger(__name__)


class ReloadException(Exception):
    
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self.body = body
        super(ReloadException, self).__init__()
    
    def get_output(self):
        return ('Status: %s\r\n' % self.status) + ''.join('%s: %s\r\n' % x for x in self.headers) + '\r\n' + self.body



def default_handler(name):
    raise ReloadException('200 OK', [('Refresh', '1'), ('Content-Type', 'text/html')], 
'''<html><head><style>
    body {
        margin: 0;
        padding: 1em;
    h1, p {
        font-weight: normal;
        margin: 0;
    }
</style></head><body">
    <h1>The <b>%r</b> module is out of date.</h1>
    <p>The FCGI server has been restarted and this request will refresh in one second.</p>
</body></html>''' % name
    )
    raise ReloadException('200 OK', [], name)



def reloader(app, packages=('nitrogen', ), func=default_handler):
    start_time = time.time()
    package_re = re.compile(r'^(%s)(\.|$)' % '|'.join(re.escape(x) for x in packages))
    name_to_path = {}
    def _reloader(environ, start):
        request_start_time = time.time()
        for name in sys.modules:
            if name not in name_to_path:
                path = None
                if package_re.match(name):
                    path = getattr(sys.modules[name], '__file__', None)
                if path and path.endswith('.pyc') and os.path.exists(path[:-1]):
                    path = path[:-1]
                name_to_path[name] = path
            else:
                path = name_to_path[name]
            try:
                if path and os.path.getmtime(path) > start_time:
                    log.info('%s has changed' % name)
                    func(name)
            except IOError as e:
                log.debug('Ignoring %n due to %r.' % e)
                name_to_path[name] = None
            
        log.debug('checked modules in %.2fms' % (1000 * (time.time() - request_start_time)))
        return app(environ, start)
    return _reloader




class FCGIMixin(object):
    
    def handler(self, req):
        try:
            return super(FCGIMixin, self).handler(req)
        
        except ReloadException as e:
            log.info('Caught %r; restarting.' % e)
            req.stdout.write(e.get_output())
        
        except SystemExit as e:
            log.exception('Caught SystemExit; restarting.')
            req.stdout.write(
                'Status: 200 OK\r\n'
                '\r\n'
                'Caught %r; restarting FCGI process.' % e)
        
        self._keepGoing = False
        return FCGI_REQUEST_COMPLETE, 0
    

class FCGIServer(FCGIMixin, _FCGIServer):

    def __init__(self, app, min_spare=1, max_spare=5, max_threads=50, **kwargs):
        kwargs.setdefault('minSpare', min_spare)
        kwargs.setdefault('maxSpare', max_spare)
        kwargs.setdefault('maxThreads', max_threads)
        super(FCGIServer, self).__init__(app, **kwargs)


class FCGIPreForkServer(FCGIMixin, _FCGIPreForkServer):

    def __init__(self, app, min_spare=1, max_spare=4, max_children=10,
        max_requests=0, setup=None, teardown=None):
        
        kwargs.setdefault('minSpare', min_spare)
        kwargs.setdefault('maxSpare', max_spare)
        kwargs.setdefault('maxChildren', max_children)
        kwargs.setdefault('maxRequests', max_requests)

        self._setup_child = setup
        self._teardown_child = teardown
        self._pid = os.getpid()

        super(FCGIPreForkServer, self).__init__(app, **kwargs)

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






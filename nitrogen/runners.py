"""WSGI application runners."""

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import threading
   
from . import local
from . import error

class thread_localizer(object):
    """WSGI middleware that stores information about the request on the
    framework thread-local object
    
    Currently stores the environment on environ, and a one-based request
    counter on request_index.
    
    """
    
    def __init__(self, app):
        self.app = app
        self.request_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        self.lock.acquire()
        self.request_count += 1
        local.request_index = self.request_count
        self.lock.release()
        local.environ = environ
        return self.app(environ, start)

def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    
    import wsgiref.handlers
    handler = wsgiref.handlers.CGIHandler()
    handler.error_status = error.DEFAULT_ERROR_HTTP_STATUS
    handler.error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    handler.error_body = error.DEFAULT_ERROR_BODY
    handler.run(thread_localizer(app))

def run_via_fcgi(app, multithreaded=True):
    """Run a web application via a FastCGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    
    from fcgi import WSGIServer
    WSGIServer(thread_localizer(app), multithreaded=multithreaded).run()

def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    from wsgiref.simple_server import make_server
    httpd = make_server(host, port, thread_localizer(app))
    if once:
        httpd.handle_request()
    else:
        httpd.serve_forever()

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
    
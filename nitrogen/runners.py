"""WSGI application runners."""


import threading
from wsgiref.simple_server import make_server
from wsgiref.handlers import CGIHandler

from flup.server.fcgi import WSGIServer as FCGIHandler

from .logs import setup_logging
from . import error


def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    
    handler = CGIHandler()
    handler.error_status = error.DEFAULT_ERROR_HTTP_STATUS
    handler.error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    handler.error_body = error.DEFAULT_ERROR_BODY
    handler.run(setup_logging(app))

def run_via_fcgi(app, multithreaded=True):
    """Run a web application via a FastCGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    
    FCGIHandler(setup_logging(app), multithreaded=multithreaded).run()

def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    httpd = make_server(host, port, setup_logging(app))
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



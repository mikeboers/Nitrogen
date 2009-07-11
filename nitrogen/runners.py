"""WSGI application runners."""

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)
    
from . import local
from .request import Request

def wrap_wsgi_style(app):
    def inner(environ, start):
        local.environ = environ
        local.start = start
        return app(environ, start)
    return inner

def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(wrap_wsgi_style(app))

def run_via_fcgi(app, multithreaded=True):
    """Run a web application via a FastCGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    
    from fcgi import WSGIServer
    WSGIServer(wrap_wsgi_style(app), multithreaded=multithreaded).run()

def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    from wsgiref.simple_server import make_server
    httpd = make_server(host, port, wrap_wsgi_style(app))
    if once:
        httpd.handle_request()
    else:
        httpd.serve_forever()

if __name__ == '__main__':
    
    def app(env, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'Hello, world!\n'
    
    import random
    
    port = random.randrange(8000, 9000)
    print 'Starting on port %d.' % port
    
    run_via_socket(app, port=port, once=True)
    
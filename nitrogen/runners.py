"""WSGI application runners."""

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)
    
from .middlewear.setup_local import setup_local

def _wrap(app):
    return setup_local(app)

def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    
    import wsgiref.handlers
    wsgiref.handlers.CGIHandler().run(_wrap(app))

def run_via_fcgi(app, multithreaded=True):
    """Run a web application via a FastCGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
        multithreaded -- Run this application in a multithreaded environment
            if nessesary. Will be running several copies of the app at once 
            if the server is under load.
    """
    
    from fcgi import WSGIServer
    WSGIServer(_wrap(app), multithreaded=multithreaded).run()

def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    from wsgiref.simple_server import make_server
    httpd = make_server(host, port, _wrap(app))
    if once:
        httpd.handle_request()
    else:
        httpd.serve_forever()

if __name__ == '__main__':
    
    def app(env, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'Hello, world!\n'
    
    run_via_socket(app, once=True)
    
"""WSGI application runners."""


import logging

from .wsgi import CGIHandler, FCGIThreadHandler, FCGIForkHandler, SocketHandler


log = logging.getLogger(__name__)


def run_via_cgi(app):
    """Run a web application via the CGI interface of a web server.
    
    Parameters:
        app -- The WSGI app to run.
    """
    log.warning('run_via_cgi is depreciated')
    CGIHandler(app).run()


def run_via_fcgi_thread(app, **kwargs):    
    log.warning('run_via_fcgi_thread is depreciated')
    FCGIThreadHandler(app, **kwargs).run()


def run_via_fcgi_fork(app, **kwargs):
    log.warning('run_via_fcgi_fork is depreciated')
    FCGIForkHandler(app, **kwargs).run()
    

run_via_fcgi = run_via_fcgi_thread


def run_via_socket(app, host='', port=8000, once=False):
    """Run a web aplication directly via a socket.
    
    Parameters:
        app -- The WSGI app to run.
        host -- What host to run on. Defaults to a wildcard.
        port -- What port to accept connections to.
        once -- Only accept a single connection.
    """
    
    log.warning('run_via_socket is depreciated')
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



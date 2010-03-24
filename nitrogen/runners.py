"""WSGI application runners.

This is only here to be backwards compatible with my earlier sites.

"""


from .wsgi.servers import (CGIServer, FCGIServer, FCGIPreForkServer, SocketServer)


def run_via_cgi(app):
    CGIServer(app).run()


def run_via_fcgi(app, **kwargs):    
    FCGIServer(app, **kwargs).run()


def run_via_fcgi_fork(app, **kwargs):
    FCGIPreForkServer(app, **kwargs).run()


def run_via_socket(app, host='', port=8000, once=False):
    handler = SocketServer(app, host, port)
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



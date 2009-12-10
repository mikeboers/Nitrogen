"""WSGI application runners.

This is only here to be backwards compatible with my earlier sites.

"""


from .wsgi.servers import (CGIServer, FCGIThreadServer, FCGIThreadPoolServer,
    FCGIForkServer, SocketServer)


def run_via_cgi(app):
    CGIServer(app).run()


def run_via_fcgi_thread(app, **kwargs):    
    FCGIThreadServer(app, **kwargs).run()


def run_via_fcgi_thread_pool(app, **kwargs):    
    FCGIThreadPoolServer(app, **kwargs).run()
    

def run_via_fcgi_fork(app, **kwargs):
    FCGIForkServer(app, **kwargs).run()
    

run_via_fcgi = run_via_fcgi_thread


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



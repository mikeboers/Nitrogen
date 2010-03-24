"""WSGI application runners.

This is only here to be backwards compatible with my earlier sites.

"""


def run_via(name, *args, **kwargs):
    import sys
    self = sys.modules[__name__]
    name = 'run_via_' + name
    runner = getattr(self, name)
    runner(*args, **kwargs)
    
def run_via_cgi(app):
    from .server.cgi import CGIServer
    CGIServer(app).run()


def run_via_fcgi(app, **kwargs):
    from .server.fcgi import FCGIServer
    FCGIServer(app, **kwargs).run()


def run_via_fcgi_fork(app, **kwargs):
    from .server.fcgi import FCGIPreForkServer
    FCGIPreForkServer(app, **kwargs).run()


def run_via_socket(app, host='', port=8000, once=False):
    from .server.socket import SocketServer
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



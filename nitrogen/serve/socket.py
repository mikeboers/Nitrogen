from wsgiref.simple_server import make_server as _make_server
        
class SocketServer(object):

    def __init__(self, app, host='', port=8000):
        self.app = app
        self.host = host
        self.port = port

    def _wrapped_app(self, environ, start):
        environ['REQUEST_URI'] = environ['PATH_INFO']
        return self.app(environ, start)
    
    def make_server(self):
        return _make_server(self.host, self.port, self._wrapped_app)

    def run_once(self):
        try:
            self.make_server().handle_request()
        except KeyboardInterrupt:
            pass

    def run(self):
        print 'Running on %s:%s.' % (self.host, self.port)
        try:
            self.make_server().serve_forever()
        except KeyboardInterrupt:
            pass
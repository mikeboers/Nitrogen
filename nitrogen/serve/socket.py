from wsgiref.simple_server import make_server as _make_server
        
class SocketServer(object):

    def __init__(self, app, host='', port=8000):
        self.app = app
        self.host = host
        self.port = port

    def make_server(self):
        return _make_server(self.host, self.port, self.app)

    def run_once(self):
        self.make_server().handle_request()

    def run(self):
        print 'Running on %s:%s.' % (self.host, self.port)
        self.make_server().serve_forever()
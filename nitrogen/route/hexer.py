
from .base import Router

class Hexer(Router):
    
    def __init__(self, app):
        self.app = app
    
    def route_step(self, path):
        try:
            path = path[1:].decode('hex')
        except:
            pass
        return self.app, path, {}
    
    def generate_step(self, data):
        return '', self.app
    
    def modify_path(self, path):
        print 'Hexer.modify_path', path
        return '/' + path.encode('hex')


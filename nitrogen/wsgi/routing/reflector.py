"""nitrogen.wsgi.routing.reflector module."""

from . import get_route_segment

class Reflector(object):
    
    def do_404(self, environ, start):
        raise NotImplemented()
    
    def __call__(self, environ, start):
        segment = get_route_segment(environ) or 'index'
        method_name = 'do_' + segment
        if not hasattr(self, method_name):
            return self.do_404(environ, start)
        method = getattr(self, method_name)
        return method(environ, start)
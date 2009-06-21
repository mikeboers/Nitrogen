"""nitrogen.wsgi.routing.reflector module."""

from . import get_routed, get_route_segment, NotFoundError

class Reflector(object):
    
    def __call__(self, environ, start):
        segment = get_route_segment(environ) or 'index'
        method_name = 'do_' + segment
        if not hasattr(self, method_name):
            raise NotFoundError(get_routed(environ))
        method = getattr(self, method_name)
        return method(environ, start)
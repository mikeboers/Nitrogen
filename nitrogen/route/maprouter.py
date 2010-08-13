
from .core import Router, RoutingStep, GenerationStep


class MapRouter(Router, dict):
    
    def __init__(self, route_key='map_key'):
        self.route_key = route_key
    
    def __repr__(self):
        return '<%s.%s:%r>' % (__name__, self.__class__.__name__,
            sorted(self.keys()))
    
    def register(self, prefix, child=None):
        prefix = str(prefix)
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        if child is not None:
            dict.__setitem__(self, prefix, child)
            return child
        def MapRouter_register(child):
            self.register(prefix, child)
        return MapRouter_register
    
    __setitem__ = register

    def update(self, *args):
        for arg in args:
            for k, v in arg.iteritems():
                self.register(k, v)
    
    def route_step(self, path):
        for prefix, child in self.iteritems():
            if path == prefix or path.startswith(prefix) and path[len(prefix)] == '/':
                return RoutingStep(
                    next=child,
                    path=path[len(prefix):],
                    data={self.route_key:prefix},
                )
    
    def generate_step(self, data):
        prefix = data.get(self.route_key)
        if prefix is None:
            return
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        if prefix in self:
            return GenerationStep(
                segment=prefix,
                next=self[prefix],
            )



    

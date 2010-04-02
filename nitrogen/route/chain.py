
from . import core

class Chain(core.Router, list):
    
    def __init__(self, *args):
        self.extend(args)
    
    def route_step(self, path):
        for router in self:
            x = router.route_step(path)
            if x is not None:
                return x
    
    def generate_step(self, data):
        for router in self:
            x = router.generate_step(path)
            if x is not None:
                return x
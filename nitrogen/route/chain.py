
from ..http.status import HttpNotFound

class Chain(list):
    
    def __init__(self, *args):
        self.extend(args)
    
    def __call__(self, environ, start):
        for router in self:
            try:
                return router(environ, start)
            except HttpNotFound:
                pass
        raise HttpNotFound()

from threading import local as _local

from . import route

class AppCore(object):
    
    def __init__(self, *args, **kwargs):
        super(AppCore, self).__init__(*args, **kwargs)
        self._locals = []
        
        router = route.ReRouter()
        self.router = route.Chain([router])
        self.route = router.register
        
    def local(self):
        obj = _local()
        self._locals.append(obj)
        return obj
    
    def clear_locals(self):
        for obj in self._locals:
            obj.__dict__.clear()
    
    def __call__(self, environ, start):
        return self.router(environ, start)


class AppDBMixin(object):
    pass

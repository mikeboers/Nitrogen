
import collections
from werkzeug.local import release_local, Local, LocalManager, LocalStack, allocate_lock
from .proxy import Proxy

class Local(Local):

    # Just adding a __dict__ property to the object.
    
    def __init__(self):
        super(Local, self).__init__()
        object.__setattr__(self, '__storage__', collections.defaultdict(dict))
    
    @property
    def __dict__(self):
        return self.__storage__[self.__ident_func__()]
    
    def __call__(self, name):
        return Proxy(lambda: getattr(self, name))


class LocalManager(LocalManager):
    
    def local(self):
        obj = Local()
        self.locals.append(obj)
        return obj
    
    def stack(self):
        obj = LocalStack()
        self.locals.append(obj)
        return obj


class LocalStack(LocalStack):
    def __call__(self):
        def _lookup():
            rv = self.top
            if rv is None:
                raise RuntimeError('object unbound')
            return rv
        return Proxy(_lookup)
    
def LocalProxy(local, name=None):
    if name is None:
        return Proxy(local)
    return Proxy(lambda: getattr(local, name))
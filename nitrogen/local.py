
import collections
from werkzeug.local import release_local, Local, LocalManager, LocalStack, allocate_lock, get_ident
from .proxy import Proxy

class Local(Local):
    
    # We are extending this class for the only purpose of adding a __dict__
    # attribute, so that this will work nearly identically to the builtin
    # threading.local class.
    
    # Not adding any more attributes, but we don't want to actually add a dict.
    __slots__ = ()
    
    def __init__(self):
        super(Local, self).__init__()
        object.__setattr__(self, '__storage__', collections.defaultdict(dict))
    
    @property
    def __dict__(self):
        # The __ident_func__ attribute is added after the 0.6.2 release (at
        # this point it is still in the development branch). This lets us
        # work with both versions.
        try:
            return self.__storage__[self.__ident_func__()]
        except AttributeError:
            return self.__storage__[get_ident()]
    
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
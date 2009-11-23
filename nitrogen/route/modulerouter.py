
# Setup path for local evaluation.
# When copying to another file, just change the parameter to be accurate.
if __name__ == '__main__':
    def __local_eval_fix(package):
        global __package__
        import sys
        __package__ = package
        sys.path.insert(0, '/'.join(['..'] * (1 + package.count('.'))))
        __import__(__package__)
    __local_eval_fix('nitrogen.route')


import os
import re
import logging

from ..uri.path import Path
from ..http.status import HttpNotFound
from .tools import get_unrouted, set_unrouted


log = logging.getLogger(__name__)


class Module(object):
    
    def __init__(self, router, module):
        self.router = router
        self.module = module
        self.app = None
        self.last_mtime = self.getmtime()
        
        self.reload()
    
    def getmtime(self):
        return os.path.getmtime(self.module.__file__)
    
    def reload(self, force=False):
        if force or self.router.reload:
            mtime = self.getmtime()
            if self.last_mtime != mtime:
                self.last_mtime = mtime
                self.app = None
                log.debug('reloading controller module %r' % self.module.__name__)
                reload(self.module)
        if self.app is None:
            self.app = getattr(self.module, self.router.app_key, None)
            if self.app is None:
                msg = 'could not find app %r on controller module %r' % (
                    self.app_key, self.module.__name__)
                log.debug(msg)
                raise HttpNotFound(msg)
    
    def __call__(self, environ, start):
        self.reload()
        return self.app(environ, start)


class ModuleRouter(object):
    
    def __init__(self, app_key='app', package='', default='index',
        reload=False):
        
        self.app_key = app_key
        self.package = package
        self.default = default
        self.reload = reload
        self._modules = {}
    
    def __call__(self, environ, start):
        
        unrouted = Path(get_unrouted(environ))
        segment = unrouted[0] if unrouted else self.default
        name = '.'.join(filter(None, self.package.split('.') + [segment]))
        
        if name not in self._modules:
            try:
                raw_module = __import__(name, fromlist=['nonempty'])
            except ImportError as e:
                # This is my ugly attempt to only throw a 404 if this import
                # fails, and not some import that this impor triggers.
                if e.args[0] == 'No module named %s' % segment:
                    raise HttpNotFound('could not import controller module %r: %r' % (name, e))
                else:
                    raise
            self._modules[name] = Module(router=self, module=raw_module)
        
        module = self._modules[name]
        
        if unrouted:
            unrouted.pop(0)
            unrouted = str(unrouted)
        else:
            unrouted = ''
        set_unrouted(environ, unrouted=unrouted, router=self)
        
        return module(environ, start)



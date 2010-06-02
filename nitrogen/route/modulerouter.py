
from pprint import pprint
from webtest import TestApp
import logging
import os
import re

from . import core
from ..http.status import HTTPNotFound
from ..uri.path import Path


log = logging.getLogger(__name__)


class Module(core.Router):
    
    def __init__(self, router, module):
        self.router = router
        self.module = module
        self._app = None
        self.last_mtime = self.getmtime()
    
    def getmtime(self):
        return os.path.getmtime(self.module.__file__)
    
    @property
    def app(self):
        if self.router.reload:
            mtime = self.getmtime()
            if self.last_mtime != mtime:
                self.last_mtime = mtime
                self._app = None
                log.debug('reloading controller module %r' % self.module.__name__)
                reload(self.module)
        if self._app is None:
            # I want to make this throw an error, but I fear breaking some
            # sites. Do it in the next version.
            self._app = getattr(self.module, self.router.app_key, None)
            if self._app is None:
                msg = 'could not find app %r on controller module %r' % (
                    self.router.app_key, self.module.__name__)
                log.debug(msg)
        return self._app
        
    def route_step(self, path):
        # log.debug('%s.route_step(%r)' % (self, path))
        # log.debug('module step to %r' % self.app)
        return self.app, path, {}
    
    def generate_step(self, data):    
        # logging.debug('\tModule.generate_step(%r, %r)' % (self, data))
        # logging.debug('\t%r' % self.app)
        return '', self.app
    
    def __repr__(self):
        return '<%s.%s of %s>' % (self.__class__.__module__, self.__class__.__name__, self.module.__name__)


class ModuleRouter(core.Router):
    
    def __init__(self, app_key='__app__', package='', default='index',
        reload=False, route_key='controller'):
        
        self.app_key = app_key
        self.package = package
        self.default = default
        self.reload = reload
        self.route_key = route_key
        
        self._modules = {}
    
    
    def route_step(self, path):
        
        path = Path(path)
        segment = path[0] if path else self.default
        segment = re.sub(r'[^a-zA-Z0-9_]+', '_', segment)
        name = '.'.join(filter(None, self.package.split('.') + [segment]))
        
        # log.debug('routing %r' % name)
        
        if name not in self._modules:
            try:
                raw_module = __import__(name, fromlist=['nonempty'])
            except ImportError as e:
                # This is my ugly attempt to only throw a 404 if this import
                # fails, and not some import that this impor triggers.
                if e.args[0] == 'No module named %s' % segment:
                    log.info('could not import controller module %r: %r' % (name, e))
                    return
                else:
                    raise
            self._modules[name] = Module(router=self, module=raw_module)
        
        module = self._modules[name]
        
        if path:
            path.pop(0)
            path = str(path)
        else:
            path = ''
        
        res = module, path, {self.route_key: segment}
        # log.debug('returning %r' % (res, ))
        return res
    
    def generate_step(self, data):
        # logging.debug('ModuleRouter.generate_step(%r, %r)' % (self, data))
        if self.route_key not in data:
            return
        segment = data.get(self.route_key)
        x = self.route_step(segment)
        # logging.debug('\t%r' % (x, ))
        if not x:
            return
        return '/' + segment, x[0]




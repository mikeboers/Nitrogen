
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

from .tools import *
from ..uri.path import Path

log = logging.getLogger(__name__)


class Module(object):
    
    def __init__(self, router, module, app_key):
        self.router = router
        self.module = module
        self.app = None
        self.mtime = None
    
    def __call__(self, environ, start):
        if self.router.reload:
            mtime = os.path.getmtime(self.module.__path__)
            if self.mtime is None or self.mtime != mtime:
                self.mtime = mtime
                self.app = None
                log.debug('reloading module %r' % self.module.__name__)
                reload(self.module)
        if self.app is None:
            self.app = getattr(self.module, self.router.app_key, None)
            if self.app is None:
                msg = 'could not find app %r on module %r' % (
                    self.app_key, self.module.__name__)
                log.error(msg)
                raise HttpNotFound(msg)
        return self.app(environ, start)


class ModuleRouter(object):
    
    def __init__(self, app_key='app', default='index', reload=False):
        """..."""
        self.app_key = app_key
        self.default = default
        self.reload = reload
        
        self.modules = {}
    
    def __call__(self, environ, start):
        
        unrouted = Path(get_unrouted(environ))
        name = unrouted[0] if unrouted else self.default
        path = self.build_path(name)
        
        if path not in self.apps:
            logging.debug("Loading app %r at %r." % (name, path))
            self.load_app(environ, path)
        if self.reload_modifications and os.path.getmtime(path) != self.apps[path][0]:
            logging.debug("App %r modified. Reloading." % name)
            self.load_app(environ, path)
        
        # Move the segment from unrouted to routed.
        get_routed(environ).append(unrouted.pop(0) if unrouted else None)
        
        logging.info('Routing %r...' % name)
        return self.apps[path][1](environ, start)
        

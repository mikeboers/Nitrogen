"""Module for wsgi dispatchers."""

import os
import re

from . import get_unrouted

class Directory(object):
    
    def __init__(self, path, app_key='app'):
        self.path = path
        self.app_key = app_key
        self.apps = {}
    
    def build_path(self, name):
        return '%s%s.py' % (self.path, name)
    
    def load_app(self, path):
        if not os.path.exists(path):
            raise ValueError("App does not exist at %r." % path)
        scope = {}
        execfile(path, scope)
        if self.app_key not in scope:
            raise ValueError("App not found in %r by key %r." % (path, self.app_key))
        self.apps[path] = (os.path.getmtime(path), scope[self.app_key])
    
    def __call__(self, environ, start):
        path = get_unrouted(environ)
        name = path.pop(0) if path else ''
        name = name if name else 'index'
        path = self.build_path(name)
        
        try:
            if path not in self.apps:
                self.load_app(path)
        except Exception as e:
            # DO 404 here!
            start('404 Not Found', [('Content-Type', 'text/plain')])
            return ['Cant find it!\n\n', str(e)]
        
        if os.path.getmtime(path) != self.apps[path][0]:
            self.load_app(path)
        
        return self.apps[path][1](environ, start)
        
    
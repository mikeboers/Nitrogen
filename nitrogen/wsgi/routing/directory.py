"""Module for wsgi dispatchers."""

import os
import re

from . import get_routed, get_route_segment, NotFoundError

class Directory(object):
    
    def __init__(self, path, app_key='app'):
        self.path = path
        self.app_key = app_key
        self.apps = {}
    
    def build_path(self, name):
        return '%s%s.py' % (self.path, name)
    
    def load_app(self, environ, path):
        if not os.path.exists(path):
            raise NotFoundError(str(get_routed(environ)), 'Could not find file.')
        scope = {}
        execfile(path, scope)
        if self.app_key not in scope:
            raise NotFoundError(str(get_routed(environ)), 'Could not find app in module.')
        self.apps[path] = (os.path.getmtime(path), scope[self.app_key])
    
    def __call__(self, environ, start):
        name = get_route_segment(environ) or 'index'
        path = self.build_path(name)
        
        if path not in self.apps:
            self.load_app(environ, path)
        if os.path.getmtime(path) != self.apps[path][0]:
            self.load_app(environ, path)
        
        return self.apps[path][1](environ, start)
        
    
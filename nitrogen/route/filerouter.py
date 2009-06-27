"""Module file based router.

A File router is initialized with a path. When it is called (as a WSGI app)
it takes the first unrouted segment of the path and looks for a python file
that corresponds to the base path and the segment (ie.
path + segment + '.py'). It executes that file, and looks for an
object by the name of the app_key attribute (defaults to "app") of the router.

The router keeps an eye on the modification time of the python file, to reload
it if it changes.

Note that the path is not joined to the segment (with os.path.join), but it is
simply contatenated.

"""

import os
import re
import logging

from . import get_routed, get_route_segment, NotFoundError

log = logging.getLogger(__name__)

class FileRouter(object):
    
    def __init__(self, path, app_key='app', reload_modifications=True):
        """Initialize the file router."""
        self.path = path
        self.app_key = app_key
        self.apps = {}
        self.reload_modifications = reload_modifications
    
    def build_path(self, name):
        return "%s%s.py" % (self.path, name)
    
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
            log.debug("Loading app %r at %r." % (name, path))
            self.load_app(environ, path)
        if self.reload_modifications and os.path.getmtime(path) != self.apps[path][0]:
            log.debug("App %r modified. Reloading." % name)
            self.load_app(environ, path)
        
        logging.info('Routing %r...' % name)
        return self.apps[path][1](environ, start)
        
    
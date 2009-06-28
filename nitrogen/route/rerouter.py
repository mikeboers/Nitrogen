"""Pattern matching router.

You must register patterns along with the apps that will be triggered if the
patterns match. Any match groups will be sent along as arguments after start
and environ.

The first pattern to match wins (from order of registration).

This router does NOT maintain the (un)routed path elements of the environ.
Therefore, it is not safe to use this before any other routers. It is suitable
as the last routing (or into another set of rerouters).

"""

import re
import logging

from . import get_routed, get_unrouted, NotFoundError

class ReRouter(object):
    
    def __init__(self, default=None):
        self._apps = []
        self.default = default
        
    def register(self, pattern, app=None):
        """Register directly, or use as a decorator."""
        if app:
            self._apps.append((re.compile(pattern), app))
            return
        
        # And the decorator
        def decorator(app):
            self.register(pattern, app)
            return app
        return decorator
    
    def __call__(self, environ, start):
        path = str(get_unrouted(environ))
        logging.debug('Looking for match on %r.' % path)
        for pattern, app in self._apps:
            m = pattern.search(path)
            if m is not None:
                return app(environ, start, *m.groups())
        if self.default:
            return self.default(environ, start)
        raise NotFoundError(get_routed(environ))
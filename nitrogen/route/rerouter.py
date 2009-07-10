"""Pattern matching router.

You must register patterns along with the apps that will be triggered if the
patterns match. Any match groups will be sent along as arguments after start
and environ.

The first pattern to match wins (from order of registration).

This router does maintain the nitrogen.path values in the environ, but only
moves the part that it explicitly removed. Therefore a slash may prefix the
unrouted path if you are not careful, and so the unrouted path will then be
absolute (and all the fun that goes with that. Ie. you will be able to pop off
the next segment and the uri remain absolute.)

You have been warned!

"""

import re
import logging

# Setup path for local evaluation.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

from tools import *
from ..uri import Path

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
                
                # Update the routing information.
                # NOTE that 
                environ['nitrogen.path.unrouted'] = Path(path[m.end():])
                get_routed(environ).append(m.group())
                
                return app(environ, start, *m.groups())
        if self.default:
            return self.default(environ, start)
        raise_not_found_error(environ, 'Could not find match.')
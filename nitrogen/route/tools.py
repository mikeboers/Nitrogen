"""Package for easy routing of requests into request handlers (or WSGI apps.)"""

# Setup path for local evaluation.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

from ..uri import URI
from ..uri.path import Path

UNROUTED_ENVIRON_KEY = 'nitrogen.path.unrouted'
ROUTED_ENVIRON_KEY = 'nitrogen.path.routed'

def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if UNROUTED_ENVIRON_KEY not in environ:
        path = URI(environ.get('REQUEST_URI', '').strip('/')).path
        path.remove_dot_segments()
        environ[UNROUTED_ENVIRON_KEY] = path
    return environ[UNROUTED_ENVIRON_KEY]

def get_routed(environ):
    if ROUTED_ENVIRON_KEY not in environ:
        environ[ROUTED_ENVIRON_KEY] = []
    return environ[ROUTED_ENVIRON_KEY]

def get_route_segment(environ):
    """Returns the next segment of the requested URI to be routed."""
    unrouted = get_unrouted(environ)
    if unrouted:
        segment = unrouted.pop(0)
        record_routed_segment(environ, segment)
        return segment
    return None

def record_routed_segment(environ, segment):
    get_routed(environ).append(segment)

class NotFoundError(ValueError):
    def __init__(self, *args, **kwargs):
        ValueError.__init__(self, *args, **kwargs)

class Chain(list):
    
    def __init__(self, *args):
        self.extend(args)
    
    def __call__(self, environ, start):
        for router in self:
            try:
                return router(environ, start)
            except NotFoundError:
                pass
        raise NotFoundError

        
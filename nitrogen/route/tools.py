"""Package for easy routing of requests into request handlers (or WSGI apps.)"""


# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen.route'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

from ..uri import URI
from ..uri.path import Path

UNROUTED_ENVIRON_KEY = 'nitrogen.path.unrouted'
ROUTED_ENVIRON_KEY = 'nitrogen.path.routed'

def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if UNROUTED_ENVIRON_KEY not in environ:
        path = URI(environ.get('REQUEST_URI', '').strip('/')).path
        path.remove_dot_segments()
        path.absolute = True
        environ[UNROUTED_ENVIRON_KEY] = path
    return environ[UNROUTED_ENVIRON_KEY]

def get_routed(environ):
    if ROUTED_ENVIRON_KEY not in environ:
        environ[ROUTED_ENVIRON_KEY] = []
    return environ[ROUTED_ENVIRON_KEY]

class NotFoundError(ValueError):
    """Please do not raise this yourself. Use raise_not_found_error instead
    as it will automatically add the unrouted and routed segments to the args.
    """
    pass

def raise_not_found_error(environ, *args):
    raise NotFoundError(get_unrouted(environ), get_routed(environ), *args)

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



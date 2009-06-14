"""nitrogen.wsgi.routing package."""

from ...uri import URI

UNROUTED_ENVIRON_KEY = 'nitrogen.unrouted'

def get_unrouted(environ):
    if UNROUTED_ENVIRON_KEY not in environ:
        path = URI(environ.get('REQUEST_URI', '')).path
        path.remove_dot_segments()
        environ[UNROUTED_ENVIRON_KEY] = path
    return environ[UNROUTED_ENVIRON_KEY]
    
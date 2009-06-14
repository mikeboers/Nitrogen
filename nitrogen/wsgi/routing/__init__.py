"""nitrogen.wsgi.routing package."""

from ...uri import URI

UNROUTED_ENVIRON_KEY = 'nitrogen.unrouted'

def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if UNROUTED_ENVIRON_KEY not in environ:
        path = URI(environ.get('REQUEST_URI', '')).path
        path.remove_dot_segments()
        environ[UNROUTED_ENVIRON_KEY] = path
    return environ[UNROUTED_ENVIRON_KEY]

def get_route_segment(environ):
    """Returns the next segment of the requested URI to be routed."""
    unrouted = get_unrouted(environ)
    return unrouted.pop(0) if unrouted else None
    
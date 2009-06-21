"""nitrogen.wsgi.routing package."""

from ..uri import URI
from ..uri.path import Path

UNROUTED_ENVIRON_KEY = 'nitrogen.path.unrouted'
ROUTED_ENVIRON_KEY = 'nitrogen.path.routed'

def get_unrouted(environ):
    """Returns the unrouted portion of the requested URI."""
    if UNROUTED_ENVIRON_KEY not in environ:
        path = URI(environ.get('REQUEST_URI', '')).path
        path.remove_dot_segments()
        environ[UNROUTED_ENVIRON_KEY] = path
    return environ[UNROUTED_ENVIRON_KEY]

def get_routed(environ):
    if ROUTED_ENVIRON_KEY not in environ:
        environ[ROUTED_ENVIRON_KEY] = Path('/')
    return environ[ROUTED_ENVIRON_KEY]

def get_route_segment(environ):
    """Returns the next segment of the requested URI to be routed."""
    unrouted = get_unrouted(environ)
    if unrouted:
        segment = unrouted.pop(0)
        get_routed(environ).append(segment)
        return segment
    return None

class NotFoundError(ValueError):
    pass
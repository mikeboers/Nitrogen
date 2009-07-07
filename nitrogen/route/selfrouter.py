"""Reflection based WSGI router.

This class first pulls off an unrouted segment that it will handle. Then, it
looks for an attribute on itself named "do_<segment>", and calls it.

If it can't find anything, it throws a NotFound error.

It is written so that you can nest reflectors.

"""

from .tools import get_routed, get_route_segment, NotFoundError

class SelfRouter(object):
    
    def __init__(self, environ, start):
        self.environ = environ
        self.start = start
    
    def __iter__(self):
        segment = get_route_segment(self.environ) or 'index'
        method_name = 'do_' + segment
        if not hasattr(self, method_name):
            raise NotFoundError('Could not find match.')
        method = getattr(self, method_name)
        for x in method(self.environ, self.start):
            yield x
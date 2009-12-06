"""Reflection based WSGI router.

This class first pulls off an unrouted segment that it will handle. Then, it
looks for an attribute on itself named "do_<segment>", and calls it.

If it can't find anything, it throws a NotFound error.

It is written so that you can nest reflectors.

"""


from . import tools

class SelfRouter(object):
    
    def __init__(self, environ, start):
        self.environ = environ
        self.start = start
    
    def __iter__(self):
        unrouted = get_unrouted(environ)
        name = unrouted[0] if unrouted else 'index'
        name = 'do_' + name
        if not hasattr(self, name):
            raise_not_found_error(environ, 'Could not find match.')
        
        # Move segment from unrouted to routed.
        get_routed(environ).append(unrouted.pop(0) if unrouted else None)
        
        # Run the found app.
        app = getattr(self, name)
        for x in app(self.environ, self.start):
            yield x


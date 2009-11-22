"""Reflection based WSGI router.

This class first pulls off an unrouted segment that it will handle. Then, it
looks for an attribute on itself named "do_<segment>", and calls it.

If it can't find anything, it throws a NotFound error.

It is written so that you can nest reflectors.

"""

# Setup path for local evaluation.
# When copying to another file, just change the parameter to be accurate.
if __name__ == '__main__':
    def __local_eval_fix(package):
        global __package__
        import sys
        __package__ = package
        sys.path.insert(0, '/'.join(['..'] * (1 + package.count('.'))))
        __import__(__package__)
    __local_eval_fix('nitrogen.route')

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


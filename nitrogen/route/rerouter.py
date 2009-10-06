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

import re
import logging

from webtest import TestApp

from . import tools
from ..uri import Path
from ..status import HttpNotFound

log = logging.getLogger(__name__)


def compile_named_groups(raw, default_pattern='[^/]+?'):
    def callback(match):
        name = match.group(1)
        pattern = match.group(2)
        if pattern is None:
            if default_pattern is None:
                return match.group(0)
            pattern = default_pattern
        return '(?P<%s>%s)' % (name, pattern)
    return re.sub(r'{([a-zA-Z_]\w*)(?::(.+?))?}', callback, raw)


def extract_named_groups(match):
    kwargs = match.groupdict()
    named_spans = set(match.span(k) for k in kwargs)
    args = [x for i, x in enumerate(match.groups()) if match.span(i + 1) not in named_spans]
    return args, kwargs


class ReRouter(object):
    
    def __init__(self, default=None):
        self._apps = []
        self.default = default
        
    def register(self, pattern, app=None):
        """Register directly, or use as a decorator."""
        
        # We are being used directly here.
        if app:
            pattern = compile_named_groups(pattern)
            self._apps.append((re.compile(pattern, re.X), app))
            return
        
        # We are not being used directly, so return a decorator to do the
        # work later.
        def decorator(app):
            self.register(pattern, app)
            return app
        return decorator
    
    def __call__(self, environ, start):
        path = tools.get_unrouted(environ)
        log.debug('matching on %r' % path)
        for pattern, app in self._apps:
            m = pattern.search(path)
            if m is not None:
                
                unrouted = path[m.end():]
                args, kwargs = extract_named_groups(m)
                tools.set_unrouted(environ, unrouted, self, matched=m.group(0), app=app, args=args, kwargs=kwargs)
                
                return app(environ, start, *args, **kwargs)
        if self.default:
            return self.default(environ, start)
        
        raise HttpNotFound()




def test_routing_path_setup():
    
    router = ReRouter()
    
    @router.register(r'^/(one|two|three)(?=/|$)')
    def one(environ, start, number):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield number
    
    @router.register(r'^/x-{var}(?=/|$)')
    def two(environ, start, *args, **kwargs):
        output = list(router(environ, start))
        yield kwargs['var'] + '\n'
        for x in output:
            yield x
    
    app = TestApp(router)

    res = app.get('/one/two')
    assert res.body == 'one'
    assert tools.get_history(res.environ) == [
        ('/one/two', None, {}),
        ('/two', router, {'kwargs': {}, 'app': one, 'args': ['one'], 'matched': '/one'})
    ]
    
    res = app.get('/x-four/x-three/x-two/one')
    assert res.body == 'four\nthree\ntwo\none'
    assert tools.get_history(res.environ) == [
        ('/x-four/x-three/x-two/one', None, {}),
        ('/x-three/x-two/one', router, {'kwargs': {'var': 'four'}, 'app': two, 'args': [], 'matched': '/x-four'}),
        ('/x-two/one', router, {'kwargs': {'var': 'three'}, 'app': two, 'args': [], 'matched': '/x-three'}),
        ('/one', router, {'kwargs': {'var': 'two'}, 'app': two, 'args': [], 'matched': '/x-two'}),
        ('', router, {'kwargs': {}, 'app': one, 'args': ['one'], 'matched': '/one'})
    ]
    
    try:
        app.get('/does/not/exist')
        assert False
    except HttpNotFound:
        pass




if __name__ == '__main__':
    from .. import test
    test.run()
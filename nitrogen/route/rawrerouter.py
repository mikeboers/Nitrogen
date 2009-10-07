"""Regular expression matching router with a lot of control.

You must register patterns along with the apps that will be triggered if the
patterns match. Match groups will be sent along as positional or keyword
arguments depending if they are a keyword match or not.

ie: r'/(one)/{two:two}/(three)' will call:
    app(environ, start, one, three, two=two)

Keyword arguments can be specified with the normal syntax (r'(?P<name>patt)')
or with a simplified syntax (r'{name:pattern}'). '}' can be escaped in the
pattern path.

Note that the first pattern to match wins (from order of registration).

By default the pattern will match the front of the path (so a leading '/' is
required) and will match the end of the path or any segment therein. By
default it will not match in the middle of a segment. If you want to force
matching the very end include '$'. If you want to not match at the front or be
liberal about the end (don't know why) adjust the lock_front and snap_back
arguments supplied to register.

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
from pprint import pprint

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
    sub_re = re.compile(r'''
        {                           # start of keyword match
        ([a-zA-Z_]\w*)              # group 1: name
        (?::(                       # colon and group 2: pattern
        [^}\\]*(?:\\.[^}\\]*)*      # zero or more chars. } can be escaped.
        ))?                         # the colon and pattern are optional
        }
    ''', re.X)
    return re.sub(sub_re, callback, raw)


def extract_named_groups(match):
    kwargs = match.groupdict()
    named_spans = set(match.span(k) for k in kwargs)
    args = [x for i, x in enumerate(match.groups()) if match.span(i + 1) not in named_spans]
    return args, kwargs


class RawReRouter(object):
    
    def __init__(self, default=None):
        self._apps = []
        self.default = default
        
    def register(self, pattern, app=None, lock_front=True, snap_back=True):
        """Register directly, or use as a decorator.
        
        Params:
            pattern -- The pattern to match with.
            app -- The app to register. If not provided this method returns
                a decorator which can be used to register with.
            lock_front -- The pattern should match only to the front.
            snap_back -- Require the pattern to match at the end of the URI
                or at the end of a path segment.
                
        """
        
        # We are being used directly here.
        if app:
            pattern = compile_named_groups(pattern)
            if lock_front:
                pattern = '^' + pattern
            if snap_back:
                pattern += r'(?=/|$)'
            self._apps.append((re.compile(pattern, re.X), app))
            return
        
        # We are not being used directly, so return a decorator to do the
        # work later.
        def decorator(app):
            self.register(pattern, app, lock_front=lock_front,
                snap_back=snap_back)
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
                tools.set_unrouted(environ,
                    unrouted=unrouted,
                    router=self
                )
                
                return app(environ, start, *args, **kwargs)
            
        if self.default:
            return self.default(environ, start)
        
        raise HttpNotFound()




def test_routing_path_setup():
    
    router = RawReRouter()
    
    @router.register(r'/(one|two|three)')
    def one(environ, start, word):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield word
    
    @router.register(r'/x-{var}')
    def two(environ, start, *args, **kwargs):
        output = list(router(environ, start))
        yield kwargs['var'] + '\n'
        for x in output:
            yield x
    
    @router.register(r'/{key:pre\}post}')
    def three(environ, start, *args, **kwargs):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield kwargs['key']
    
    app = TestApp(router)

    res = app.get('/one/two')
    assert res.body == 'one'
    # pprint(tools.get_history(res.environ))
    assert tools.get_history(res.environ) == [
        tools.HistoryChunk(
            path='/one/two',
            unrouted='/two',
            router=router)
    ]
    
    res = app.get('/x-four/x-three/x-two/one')
    # print res.body
    assert res.body == 'four\nthree\ntwo\none'
    # pprint(tools.get_history(res.environ))
    assert tools.get_history(res.environ) == [
        tools.HistoryChunk(path='/x-four/x-three/x-two/one', unrouted='/x-three/x-two/one', router=router),
        tools.HistoryChunk(path='/x-three/x-two/one', unrouted='/x-two/one', router=router),
        tools.HistoryChunk(path='/x-two/one', unrouted='/one', router=router),
        tools.HistoryChunk(path='/one', unrouted='', router=router)
    ]
        
    try:
        app.get('/-does/not/exist')
        assert False
    except HttpNotFound:
        pass
    
    res = app.get('/x-four/x-three/x-two/one')
    # print res.body
    assert res.body == 'four\nthree\ntwo\none'
    # pprint(tools.get_history(res.environ))
    assert tools.get_history(res.environ) == [
        tools.HistoryChunk(path='/x-four/x-three/x-two/one', unrouted='/x-three/x-two/one', router=router),
        tools.HistoryChunk(path='/x-three/x-two/one', unrouted='/x-two/one', router=router),
        tools.HistoryChunk(path='/x-two/one', unrouted='/one', router=router),
        tools.HistoryChunk(path='/one', unrouted='', router=router)
    ]

    res = app.get('/pre}post')
    assert res.body == 'pre}post'



if __name__ == '__main__':
    from .. import test
    test.run()
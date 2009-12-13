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


import re
import logging
from pprint import pprint
import collections

from webtest import TestApp

from . import tools
from ..uri import Path
from ..http.status import HttpNotFound

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
    args = [match.group(0)] + [x for i, x in enumerate(match.groups()) if match.span(i + 1) not in named_spans]
    return args, kwargs


class RawReMatch(collections.Mapping):

    def __init__(self, m):
        self.m = m
        self.args, self.kwargs = extract_named_groups(m)
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return self.args[key]
        if isinstance(key, basestring):
            return self.kwargs[key]
        raise TypeError('key must be int or str')
    
    def group(self, group):
        return self.m.group(group)
    
    def __iter__(self):
        return iter(self.kwargs)
    
    def __len__(self):
        return len(self.kwargs)
    
    
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
                tools.update_route(environ,
                    unrouted=unrouted,
                    router=self,
                    data=RawReMatch(m)
                )
                return app(environ, start)
            
        if self.default:
            return self.default(environ, start)
        
        raise HttpNotFound()




def test_routing_path_setup():
    
    router = RawReRouter()
    
    @router.register(r'/(one|two|three)')
    def one(environ, start):
        word = tools.get_route(environ)[-1][1]
        start('200 OK', [('Content-Type', 'text-plain')])
        yield word
    
    @router.register(r'/x-{var}')
    def two(environ, start):
        kwargs = tools.get_route(environ)[-1]
        output = list(router(environ, start))
        yield kwargs['var'] + '\n'
        for x in output:
            yield x
    
    @router.register(r'/{key:pre\}post}')
    def three(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield tools.get_route(environ)[-1]['key']
    
    app = TestApp(router)

    res = app.get('/one/two')
    # pprint(tools.get_history(res.environ))
    tools._assert_next_history_step(res,
        before='/one/two',
        after='/two',
        router=router)
    
    res = app.get('/x-four/x-three/x-two/one')
    # print res.body
    assert res.body == 'four\nthree\ntwo\none'
    # pprint(tools.get_history(res.environ))
    tools._assert_next_history_step(res,
        before='/x-four/x-three/x-two/one', after='/x-three/x-two/one', router=router, _data={'var': 'four'})
    tools._assert_next_history_step(res,
        before='/x-three/x-two/one', after='/x-two/one', router=router)
    tools._assert_next_history_step(res,
        before='/x-two/one', after='/one', router=router)
    tools._assert_next_history_step(res,
        before='/one', after='', router=router)
    
        
    try:
        app.get('/-does/not/exist')
        assert False
    except HttpNotFound:
        pass

    res = app.get('/pre}post')
    assert res.body == 'pre}post'



if __name__ == '__main__':
    from .. import test
    test.run()

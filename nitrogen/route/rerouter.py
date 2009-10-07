
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
import hashlib
import base64
from pprint import pprint

from webtest import TestApp

from . import tools
from ..uri import Path
from ..status import HttpNotFound

log = logging.getLogger(__name__)

class Route(object):
    """
    >>> r = Route(r'/{controller}/{action}/{id:\d+}')
    >>> r
    <Route:r'/{controller}/{action}/{id:\d+}'>
    
    >>> r.match('/gallery/photo/12')[0]
    {'action': 'photo', 'controller': 'gallery', 'id': '12'}
    
    >>> r.match('/controller/action/12extra')
    >>> r.match('/controller/action/not_digits')
    
    >>> r.match('/controller/action/12/extra')
    ({'action': 'action', 'controller': 'controller', 'id': '12'}, '/extra')
    
    >>> r.build(controller='news', action='archive', id='24')
    '/news/archive/24'
    
    >>> r = Route('/gallery/{action}', controller='gallery')
    >>> m = r.match('/gallery/view')
    >>> m[0]
    {'action': 'view', 'controller': 'gallery'}
    >>> r.build(**m[0])
    '/gallery/view'
    
    >>> r = Route('/{id}', _requirements={'id': r'\d+'})
    >>> r.match('/12')[0]
    {'id': '12'}
    >>> r.match('/hi')
    
    >>> r = Route('/{id:\d+}', _parsers={'id':int})
    >>> r.match('/12')[0]
    {'id': 12}
    
    >>> r = Route('/{method:[A-Z]+}', _formatters={'method': str.upper})
    >>> r.match('/GET')[0]
    {'method': 'GET'}
    >>> r.build(method='post')
    '/POST'
    
    
    """
    
    default_pattern = '[^/]*'
    token_re = re.compile(r'''
        {                           # start of keyword match
        ([a-zA-Z_]\w*)              # group 1: name
        (?::(                       # colon and group 2: pattern
        [^}\\]*(?:\\.[^}\\]*)*      # zero or more chars. } can be escaped.
        ))?                         # the colon and pattern are optional
        }
    ''', re.X)
    
    def __init__(self, raw, **kwargs):
        
        self._raw = raw
        self._constants = kwargs
        
        self._requirements = kwargs.pop('_requirements', {})
        self._requirements = dict((k, re.compile(v + '$'))
            for k, v in self._requirements.items())
        
        self._parsers = kwargs.pop('_parsers', {})
        self._formatters = kwargs.pop('_formatters', {})
        
        self._compile()
        
    
    def __repr__(self):
        return '<Route:r%s>' % repr(self._raw).replace('\\\\', '\\')
    
    def _compile(self):
        
        self._hash_to_key = {}
        self._hash_to_pattern = {}
        
        format = self.token_re.sub(self._compile_sub, self._raw)
        
        pattern = re.escape(format)
        for hash, patt in self._hash_to_pattern.items():
            pattern = pattern.replace(hash, patt, 1)
        
        for hash, key in self._hash_to_key.items():
            format = format.replace(hash, '%%(%s)s' % key, 1)
        
        self.format = format        
        self.compiled = re.compile(pattern + r'(?=/|$)')
        
        del self._hash_to_key
        del self._hash_to_pattern
        
    def _compile_sub(self, match):
        name = match.group(1)
        patt = match.group(2) or self.default_pattern
        hash = 'x' + base64.b32encode(hashlib.md5(name).digest()).strip('=')
        self._hash_to_key[hash] = name
        self._hash_to_pattern[hash] = '(?P<%s>%s)' % (name, patt)
        return hash
    
    def match(self, value):
        m = self.compiled.match(value)
        if not m:
            return None
        
        result = self._constants.copy()
        result.update(m.groupdict())
        
        for key, pattern in self._requirements.items():
            if not key in result or not pattern.match(result[key]):
                return None
        
        for key, callback in self._parsers.items():
            if key in result:
                result[key] = callback(result[key])
        
        return result, value[m.end():]
    
    def build(self, **kwargs):
        for key, callback in self._formatters.items():
            if key in kwargs:
                kwargs[key] = callback(kwargs[key])
        return self.format % kwargs
            
        
class ReRouter(object):

    def __init__(self, default=None):
        self._apps = []
        self.default = default

    def register(self, name, pattern=None, app=None, **kwargs):
        """Register directly, or use as a decorator.

        Params:
            pattern -- The pattern to match with.
            app -- The app to register. If not provided this method returns
                a decorator which can be used to register with.
            lock_front -- The pattern should match only to the front.
            snap_back -- Require the pattern to match at the end of the URI
                or at the end of a path segment.

        """
        
        if pattern is None and app is None:
            pattern = name
            name = None
        
        # We are being used directly here.
        if app:
            route = Route(pattern, **kwargs)
            self._apps.append((route, app))
            return

        # We are not being used directly, so return a decorator to do the
        # work later.
        def decorator(app):
            self.register(name, pattern, app, **kwargs)
            return app
        return decorator

    def __call__(self, environ, start):
        path = tools.get_unrouted(environ)
        log.debug('matching on %r' % path)
        for route, app in self._apps:
            m = route.match(path)
            if m:
                kwargs, unmatched = m
                tools.set_unrouted(environ,
                    unrouted=unmatched,
                    router=self,
                    builder=self._builder,
                    args=[kwargs]
                )

                return app(environ, start, **kwargs)

        if self.default:
            return self.default(environ, start)

        raise HttpNotFound()
    
    def _builder(self, route, kwargs):
        raise NotImplemented




def test_routing_path_setup():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start, word):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield word

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start, **kwargs):
        output = list(router(environ, start))
        yield '%02d\n' % kwargs['num']
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
            router=router,
            builder=router._builder,
            args=[{'word': 'one'}])
    ]

    res = app.get('/x-4/x-3/x-2/one')
    # print res.body
    assert res.body == '04\n03\n02\none'
    # pprint(tools.get_history(res.environ))
    assert tools.get_history(res.environ) == [
        tools.HistoryChunk(path='/x-4/x-3/x-2/one', unrouted='/x-3/x-2/one', router=router, builder=router._builder, args=[{'num': 4}]),
        tools.HistoryChunk(path='/x-3/x-2/one', unrouted='/x-2/one', router=router, builder=router._builder, args=[{'num': 3}]),
        tools.HistoryChunk(path='/x-2/one', unrouted='/one', router=router, builder=router._builder, args=[{'num': 2}]),
        tools.HistoryChunk(path='/one', unrouted='', router=router, builder=router._builder, args=[{'word': 'one'}])
    ]

    try:
        app.get('/-does/not/exist')
        assert False
    except HttpNotFound:
        pass
    
    try:
        app.get('/one_extra/does-not-exist')
        assert False
    except HttpNotFound:
        pass

    res = app.get('/pre}post')
    assert res.body == 'pre}post'


if __name__ == '__main__':
    from .. import test
    test.run()

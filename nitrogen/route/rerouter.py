

import re
import logging
import hashlib
import base64
from pprint import pprint
import collections

from webtest import TestApp

from . import tools
from ..uri import Path
from ..http.status import HttpNotFound

log = logging.getLogger(__name__)

class Pattern(object):
    """
    >>> r = Pattern(r'/{controller}/{action}/{id:\d+}')
    >>> r
    <__main__.Pattern:r'/{controller}/{action}/{id:\d+}'>

    >>> r.match('/gallery/photo/12')[0]
    {'action': 'photo', 'controller': 'gallery', 'id': '12'}

    >>> r.match('/controller/action/12extra')
    >>> r.match('/controller/action/not_digits')

    >>> r.match('/controller/action/12/extra')
    ({'action': 'action', 'controller': 'controller', 'id': '12'}, '/extra')

    >>> r.format(controller='news', action='archive', id='24')
    '/news/archive/24'

    >>> r = Pattern('/gallery/{action}', controller='gallery')
    >>> m = r.match('/gallery/view')
    >>> m[0]
    {'action': 'view', 'controller': 'gallery'}
    >>> r.format(**m[0])
    '/gallery/view'

    >>> r = Pattern('/{id}', _requirements={'id': r'\d+'})
    >>> r.match('/12')[0]
    {'id': '12'}
    >>> r.match('/hi')

    >>> r = Pattern('/{id:\d+}', _parsers={'id':int})
    >>> r.match('/12')[0]
    {'id': 12}

    >>> r = Pattern('/{method:[A-Z]+}', _formatters={'method': str.upper})
    >>> r.match('/GET')[0]
    {'method': 'GET'}
    >>> r.format(method='post')
    '/POST'
    
    >>> r = Pattern('/{id:\d+}', _parsers=dict(id=int),
    ...     _formatters=dict(id='%04d'))
    >>> r.match('/123')[0]
    {'id': 123}
    >>> r.format(id=456)
    '/0456'


    """

    default_pattern = '[^/]+'
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
        self._keys = set()
        
        self._requirements = kwargs.pop('_requirements', {})
        self._requirements = dict((k, re.compile(v + '$'))
            for k, v in self._requirements.items())

        self._parsers = kwargs.pop('_parsers', {})
        self._formatters = kwargs.pop('_formatters', {})

        self._compile()


    def __repr__(self):
        return '<%s.%s:r%s>' % (__name__, self.__class__.__name__,
            repr(self._raw).replace('\\\\', '\\'))

    def _compile(self):

        self._hash_to_key = {}
        self._hash_to_pattern = {}

        format = self.token_re.sub(self._compile_sub, self._raw)

        pattern = re.escape(format)
        for hash, patt in self._hash_to_pattern.items():
            pattern = pattern.replace(hash, patt, 1)

        for hash, key in self._hash_to_key.items():
            format = format.replace(hash, '%%(%s)s' % key, 1)

        self._format = format
        self._compiled = re.compile(pattern + r'(?=/|$)')

        del self._hash_to_key
        del self._hash_to_pattern

    def _compile_sub(self, match):
        name = match.group(1)
        self._keys.add(name)
        patt = match.group(2) or self.default_pattern
        hash = 'x%s' % hashlib.md5(name).hexdigest()
        self._hash_to_key[hash] = name
        self._hash_to_pattern[hash] = '(?P<%s>%s)' % (name, patt)
        return hash

    def match(self, value):
        """Match this pattern against some text. Returns the matched data, and
        the unmatched string, or None if there is no match.
        """

        m = self._compiled.match(value)
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

    def format(self, **kwargs):
        data = self._constants.copy()
        data.update(kwargs)
        for key, formatter in self._formatters.items():
            if key in data:
                if isinstance(formatter, basestring):
                    data[key] = formatter % data[key]
                else:
                    data[key] = formatter(data[key])
        return self._format % data


class Match(collections.Mapping):

    def __init__(self, pattern, data, unmatched):
        self.pattern = pattern
        self.data = data
        self.unmatched = unmatched

    def __getitem__(self, key):
        return self.data[key]

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def format(self, **kwargs):    
        data = self.data.copy()
        data.update(kwargs)
        return self.pattern.format(**data)
    
    def generate(self, chunk, newdata, unrouted):
        # print 'Match.generate', self, chunk, newdata, unrouted
        data = self.data.copy()
        data.update(newdata)
        route_name = data.get('route_name')
        route_pair = chunk.router._name_to_pair.get(route_name)
        if route_pair:
            return route_pair[0].format(**data) + unrouted
        for pattern, app in chunk.router._apps:
            try:
                return pattern.format(**data) + unrouted
            except KeyError:
                pass
        return self.pattern.format(**data) + unrouted
    
    def _generate(self, data, unrouted):
        return self.format(**data) + unrouted


class ReRouter(object):

    def __init__(self):
        self._apps = []

    def register(self, pattern, app=None, **kwargs):
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
            pair = (Pattern(pattern, **kwargs), app)
            self._apps.append(pair)
            return

        # We are not being used directly, so return a decorator to do the
        # work later.
        def ReRouter_register(app):
            self.register(pattern, app, **kwargs)
            return app
        return ReRouter_register

    def __call__(self, environ, start):
        route = tools.get_route(environ)
        path = route.path
        # print repr(path)
        log.debug('matching on %r' % path)
        for pattern, app in self._apps:
            m = pattern.match(path)
            if m:
                kwargs, path = m
                match = Match(pattern, kwargs, path)
                route.update(path=path, router=self, data=match)
                return app(environ, start)

        raise HttpNotFound()






def test_routing_path_setup():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield tools.get_route(environ)[-1]['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        chunk = tools.get_route(environ)[-1]
        output = list(router(environ, start))
        yield '%02d\n' % chunk['num']
        for x in output:
            yield x

    @router.register(r'/{key:pre\}post}')
    def three(environ, start, *args, **kwargs):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield tools.get_route(environ)[-1]['key']

    app = TestApp(router)

    res = app.get('/one/two')
    assert res.body == 'one'
    # pprint(tools.get_history(res.environ))
    tools._assert_next_history_step(res,
            path='/two',
            router=router
    )

    res = app.get('/x-4/x-3/x-2/one')
    # print res.body
    assert res.body == '04\n03\n02\none'
    # pprint(tools.get_history(res.environ))
    tools._assert_next_history_step(res,
        path='/x-3/x-2/one', router=router, _data={'num': 4})
    tools._assert_next_history_step(res,
        path='/x-2/one', router=router, _data={'num': 3})
    tools._assert_next_history_step(res,
        path='/one', router=router, _data={'num': 2})
    tools._assert_next_history_step(res,
        path='', router=router, _data={'word': 'one'})

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


def test_route_building():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield tools.get_route(environ)[-1]['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        kwargs = tools.get_route(environ)[-1]
        start('200 OK', [('Content-Type', 'text-plain')])
        yield '%02d' % kwargs['num']

    @router.register('')
    def three(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'empty'

    app = TestApp(router)

    res = app.get('/x-1')
    route = tools.get_route(res.environ)
    print repr(res.body)
    
    res = app.get('/x-1/one/blah')
    route = tools.get_route(res.environ)
    print repr(res.body)

if __name__ == '__main__':
    import logging
    from .. import test
    test.run()

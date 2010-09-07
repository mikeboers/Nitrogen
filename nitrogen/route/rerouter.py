
from bisect import insort
import collections
import hashlib
import logging
import re

from ..uri import Path
from . import core


log = logging.getLogger(__name__)


class FormatError(ValueError):
    pass


class Pattern(object):
    """
    >>> r = Pattern(r'/{controller}/{action}/{id:\d+}')
    >>> r
    <Pattern:r'/{controller}/{action}/{id:\d+}'>

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

    >>> r = Pattern('/{action:get}/{id:\d+}', _formatters=dict(id=int))
    >>> r.match('/get/12')[0]
    {'action': 'get', 'id': '12'}
    >>> r.format(action='test', id=4)
    Traceback (most recent call last):
    ...
    FormatError: cannot match against output

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
        return '<%s:r%s>' % (self.__class__.__name__,
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

        self._parse_data(result)

        return result, value[m.end():]

    def _parse_data(self, data):
        for key, callback in self._parsers.items():
            if key in data:
                data[key] = callback(data[key])

    def _format_data(self, data):
        for key, formatter in self._formatters.items():
            if key in data:
                if isinstance(formatter, basestring):
                    data[key] = formatter % data[key]
                else:
                    data[key] = formatter(data[key])

    def format(self, **kwargs):
        data = self._constants.copy()
        data.update(kwargs)
        self._format_data(data)

        out = self._format % data

        x = self.match(out)
        if x is None:
            raise FormatError('cannot match against output')
        m, d = x
        if d:
            raise FormatError('did not match all output')

        self._parse_data(data)

        for k, v in m.iteritems():
            if k in data and data[k] != v:
                raise FormatError('got different value for %r: got %r, expected %r' % (k, v, data[k]))

        return out



class Match(collections.Mapping):

    def __init__(self, pattern, data, unmatched):
        self.pattern = pattern
        self.data = data
        self.unmatched = unmatched

    def __getitem__(self, key):
        return self.data[key]

    def __getattr__(self, name):
        return getattr(self.data, name)

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def format(self, **kwargs):
        data = self.data.copy()
        data.update(kwargs)
        return self.pattern.format(**data)


class ReRouter(core.Router):

    def __init__(self):
        self._apps = []

    def register(self, pattern, app=None, **kwargs):
        """Register directly, or use as a decorator.

        Params:
            pattern -- The pattern to match with. Should start with a '/'.
            app -- The app to register. If not provided this method returns
                a decorator which can be used to register with.

        """

        # We are being used directly here.
        if app:
            # We are creating a key here that will first respect the requested
            # priority of apps relative to each other, but in the case of
            # multiple apps at the same priority, respect the registration
            # order.
            priority = (-kwargs.pop('_priority', 0), len(self._apps))
            insort(self._apps, (priority, Pattern(pattern, **kwargs), app))
            return app

        # We are not being used directly, so return a decorator to do the
        # work later.
        def ReRouter_register(app):
            self.register(pattern, app, **kwargs)
            return app
        return ReRouter_register

    def route_step(self, path):
        for _, pattern, app in self._apps:
            m = pattern.match(path)
            if m:
                kwargs, path = m
                return core.RoutingStep(next=app, path=path, data=kwargs)

    def generate_step(self, data):
        log.debug('generate_step(%r, %r)' % (self, data))
        for _, pattern, app in self._apps:
            # Skip patterns that are not identifiable.
            if not (pattern._keys or pattern._constants):
                continue
            # Filter out unmatching constant data.
            if any(k in data and data[k] != v for k, v in
                pattern._constants.iteritems()):
                continue
            try:
                return core.GenerationStep(segment=pattern.format(**data), next=app)
            except FormatError:
                pass
                # log.exception('FormatError while generating')
            except KeyError:
                pass
                # log.exception('KeyError while generating')







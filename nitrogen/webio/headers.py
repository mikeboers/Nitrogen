"""Module for Headers and MutableHeaders objects.

Examples:

    >>> h = Headers(content_type='test/plain', content_encoding='deflate')
    >>> h
    Headers([('Content-Encoding', 'deflate'), ('Content-Type', 'test/plain')])
    >>> 'Content-Type' in h
    True
    >>> 'content type' in h
    True
    >>> 'not in h' in h
    False
    >>> h.content_type
    'test/plain'
    
    >>> h['test'] = 'not allowed'
    Traceback (most recent call last):
    ...
    TypeError: 'Headers' object does not support item assignment
    
    >>> h = MutableHeaders(a=1, b=2)
    >>> h.a
    '1'
    >>> h.A
    '1'
    >>> h['c'] = 3
    >>> h.c
    '3'
    >>> h.d = 4
    >>> h['D']
    '4'
    >>> h.append(('multi', 'first'))
    >>> h.append(('multi', 'second'))
    >>> h.multi
    'first'
    >>> h.getall('multi')
    ['first', 'second']
    
    >>> h.append = 'does this break?'
    >>> h.append # doctest: +ELLIPSIS
    <bound method MutableHeaders.append of MutableHeaders([...])>
    >>> h['append']
    'does this break?'
    
"""


import re

import multimap
        
def conform_header_name(name, titlecase=True):
    """
    
    >>> conform_header_name('Content-Type')
    'Content-Type'
    >>> conform_header_name('Content Type')
    'Content-Type'
    >>> conform_header_name('content-type')
    'Content-Type'
    >>> conform_header_name('CONTENT_TYPE')
    'Content-Type'
    >>> conform_header_name('---Content---Type---')
    'Content-Type'
    >>> conform_header_name('one')
    'One'
    >>> conform_header_name('one two three')
    'One-Two-Three'
    
    """
    name = re.sub(r'[^a-zA-Z0-9]+', ' ', name)
    chunks = name.strip().split()
    return '-'.join(chunk.title() if titlecase else chunk for chunk in chunks)

class HeaderTraits(object):
    """The additional methods on top of the [Mutable]MultiMap class for a
    header mapping."""
    def _conform_key(self, key):
        return conform_header_name(key)
    
    def _conform_value(self, value):
        return str(value)
    
    def __getattr__(self, key):
        if key not in self:
            raise AttributeError(key)
        return self[key]


class Headers(HeaderTraits, multimap.MultiMap):
    pass
class MutableHeaders(HeaderTraits, multimap.MutableMultiMap):
    pass
class DelayedMutableHeaders(HeaderTraits, multimap.DelayedMutableMultiMap):
    pass


ENVIRON_KEY = 'nitrogen.headers'

def parse_headers(environ, environ_key=ENVIRON_KEY):
    """WSGI middleware which adds a header mapping to the environment."""
    if environ_key not in environ:
        environ[environ_key] = MutableHeaders((k[5:], v) for k, v in environ.iteritems() if k.startswith('HTTP_'))
    return environ[environ_key]

if __name__ == '__main__':
    from nitrogen.test import run
    run()
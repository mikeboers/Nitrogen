"""Module for Headers and MutableHeaders objects.

This whole thing has been deprecated in favor of using a request and response
object.

Examples:

    >>> h = Headers(content_type='test/plain', content_encoding='deflate')
    >>> h
    Headers([('Content-Encoding', 'deflate'), ('Content-Type', 'test/plain')])
    >>> 'Content-Type' in h
    True
    >>> 'content_type' in h
    True
    >>> 'not in h' in h
    False
    >>> h['content-type']
    'test/plain'
    
    >>> h['test'] = 'not allowed'
    Traceback (most recent call last):
    ...
    TypeError: 'Headers' object does not support item assignment
    
    >>> h = MutableHeaders(a=1, b=2)
    >>> h.append(('multi', 'first'))
    >>> h.append(('multi', 'second'))
    >>> h.getall('multi')
    ['first', 'second']
    
"""


import re
import collections
import logging

import multimap


log = logging.getLogger(__name__)

        
def environ_name_to_header(name):
    """
    
    >>> environ_name_to_header('Content-Type')
    'Content-Type'
    >>> environ_name_to_header('content-type')
    'Content-Type'
    >>> environ_name_to_header('HTTP_CONTENT_TYPE')
    'Content-Type'
    >>> environ_name_to_header('one')
    'One'
    >>> environ_name_to_header('x-example')
    'X-Example'
    
    """
    if name.startswith('HTTP_'):
        name = name[5:]
    return name.replace('_', '-').title()


def header_name_to_environ(name):
    # log.warning(repr(name))
    name = name.replace('-', '_').upper()
    if name in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
        return name
    return 'HTTP_' + name
    

class HeaderTraits(object):
    """The additional methods on top of the [Mutable]MultiMap class for a
    header mapping."""
    
    _conform_key = staticmethod(environ_name_to_header)
    _conform_value = staticmethod(str)


class Headers(HeaderTraits, multimap.MultiMap):
    pass
class MutableHeaders(HeaderTraits, multimap.MutableMultiMap):
    pass


class EnvironHeaders(collections.MutableMapping):

    def __init__(self, environ):
        self.environ = environ

    def __getitem__(self, key):
        return self.environ[header_name_to_environ(key)]
    
    def __setitem__(self, key, value):
        self.environ[header_name_to_environ(key)] = str(value)
    
    def __delitem__(self, key):
        del self.environ[header_name_to_environ(key)]

    def __len__(self):
        # the iter is necessary because otherwise list calls our
        # len which would call list again and so forth.
        return len(list(iter(self)))

    def iteritems(self):
        for key, value in self.environ.iteritems():
            if key.startswith('HTTP_') and key not in \
               ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                yield key[5:].replace('_', '-').title(), value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                yield key.replace('_', '-').title(), value
    
    def __iter__(self):
        return iter(x[0] for x in self.iteritems())


ENVIRON_KEY = 'nitrogen.headers'


def parse_headers(environ, environ_key=ENVIRON_KEY):
    """WSGI middleware which adds a header mapping to the environment."""
    if environ_key not in environ:
        environ[environ_key] = MutableHeaders(EnvironHeaders(environ))
    return environ[environ_key]


if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
    exit()
"""

A convenient description of "uniform resource identifiers" or "data source
names".

We are attempting to (nearly) follow RFC 3986 but we may not have completely
finished, and may have made some (slight) alterations. We should be
documenting those changes as they are made.

The split function simply breaks up a URI into its components. At no time does
it do ANY decoding of the URI material.

See: http://en.wikipedia.org/wiki/Uniform_Resource_Identifier
See: http://tools.ietf.org/html/rfc3986


Encoding and decoding:

    >>> encode("This is a string.")
    'This%20is%20a%20string.'
    
    >>> encode('this/is/a/string/with/slashes')
    'this%2fis%2fa%2fstring%2fwith%2fslashes'
    
    >>> encode('this/is/a/string/with/safe/slashes', '/')
    'this/is/a/string/with/safe/slashes'
    
    >>> all_chars = ''.join(chr(x) for x in range(256));
    >>> decode(encode(all_chars)) == all_chars
    True
    
URI class usage:

    >>> uri = URI()
    >>> str(uri)
    ''
    
    >>> uri.host = 'example.com'
    >>> str(uri)
    '//example.com'
    
    >>> uri.scheme = 'https'
    >>> str(uri)
    'https://example.com'
    
    >>> uri.userinfo = ['user']
    >>> str(uri)
    'https://user@example.com'
    >>> uri.userinfo.append('password')
    >>> str(uri)
    'https://user:password@example.com'
    >>> uri.userinfo = 'a:b:c:d:e'
    >>> uri.userinfo
    <uri.Userinfo:['a', 'b', 'c', 'd', 'e']>
    >>> uri.userinfo[4] = 'f'
    >>> str(uri)
    'https://a:b:c:d:f@example.com'
    >>> uri.userinfo = ''
    >>> uri.userinfo
    <uri.Userinfo:[]>
    >>> str(uri)
    'https://example.com'
    
    >>> uri.path = ['a', 'b', 'c']
    >>> str(uri)
    'https://example.com/a/b/c'
    
    >>> uri.path = '/d/e/f'
    >>> str(uri)
    'https://example.com/d/e/f'
    
    >>> uri.query = {'a': '1', 'b': '2'}
    >>> uri.query.sort()
    >>> str(uri)
    'https://example.com/d/e/f?a=1&b=2'
    
"""

import urllib
import urlparse
import re
import collections

from transcode import *
from userinfo import Userinfo
from path import Path
from query import Query

SplitUri = collections.namedtuple('SplitUri', 'scheme userinfo host port path query fragment'.split())
ParsedUri = collections.namedtuple('ParsedUri', 'scheme userinfo host port path query fragment'.split())

def split(uri):
    """Split up a URI into its base components. Returns a SplitUri (which is a
    collections.namedtuple).
    
    The split parts have NOT been decoded in any way. This ONLY splits up the
    URI.
    
    Note that the path will always be a string, although it may be empty. If
    there is an authority part, then the host will always be a string as well,
    althought it may be empty. If there is no authority, the host will be
    none. The scheme will never be an empty string. The remaining sections
    will be a string if there delimeter is found, although they may be empty.
    They will be None if there delimiter was not found.
    
    Basic example:
    
        >>> uri = split('http://user:pass@example.com:80/path?query#fragment')
        >>> uri
        SplitUri(scheme='http', userinfo='user:pass', host='example.com', port='80', path='/path', query='query', fragment='fragment')
        >>> uri.host
        'example.com'
    
    Empty sections:
    
        >>> split('s://@:?#')
        SplitUri(scheme='s', userinfo='', host='', port='', path='', query='', fragment='')
        
        >>> split('///path')
        SplitUri(scheme=None, userinfo=None, host='', port=None, path='/path', query=None, fragment=None)
        
        >>> split('path?query#')
        SplitUri(scheme=None, userinfo=None, host=None, port=None, path='path', query='query', fragment='')
        
    """
    # Pull our the 5 major parts.
    # This regex is from Appendix B of the RFC.
    m = re.match(r'^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?', uri)
    #               12            3  4          5       6  7        8 9
    
    if not m:
        raise ValueError('Could not split uri.')
    
    ret = {
        'scheme': m.group(2),
        'path': m.group(5),
        'query': m.group(7),
        'fragment': m.group(9)
    }
    authority = m.group(4)
    if authority is not None:
        ret.update(_split_authority(authority))
    else:
        for key in 'userinfo host port'.split():
            ret[key] = None
        
    return SplitUri(**ret)

def _split_authority(authority):
    """Split up an authority part into userinfo, host, and port. Returns a dict.
    
    The split parts have NOT been decoded in any way. Also, the host will always be a string, although it may be empty. The userinfo and port section will be None if they did not exist, but they may be an empty string if their delimiter existed, but there was no content.
    
    Basic example:
        >>> _split_authority('user:pass@example.com:port')
        {'host': 'example.com', 'userinfo': 'user:pass', 'port': 'port'}
    
    Empty host:
        >>> _split_authority(':80')
        {'host': '', 'userinfo': None, 'port': '80'}
    
    Empty port:
        >>> _split_authority('example.com:')
        {'host': 'example.com', 'userinfo': None, 'port': ''}
    
    Empty userinfo:
        >>> _split_authority('@example.com')
        {'host': 'example.com', 'userinfo': '', 'port': None}
    
    """
    
    m = re.match(r'^(([^@]*)@)?([^:]*)(:(.*))?$', authority)
    #               12         3      4 5
    
    if not m:
        raise ValueError('Could not split authority.')
    
    return {
        'userinfo': m.group(2),
        'host': m.group(3),
        'port': m.group(5)
    }

class URI(object):
    def __init__(self, uri=''):
        uri = uri if isinstance(uri, SplitUri) else split(uri)
        
        self.scheme = uri.scheme and decode(uri.scheme)
        self.userinfo = uri.userinfo
        self.host = uri.host and decode(uri.host)
        self.port = uri.port and decode(uri.port)
        self.path = uri.path
        self.query = uri.query
        self.fragment = uri.fragment and decode(uri.fragment)
    
    @property
    def path(self):
        return self._path
    
    @path.setter
    def path(self, path):
        if isinstance(path, Path):
            self._path = path
        else:
            self._path = Path(path)
    
    @property
    def query(self):
        return self._query

    @query.setter
    def query(self, query):
        if isinstance(query, Query):
            self._query = query
        else:
            self._query = Query(query)

    @property
    def userinfo(self):
        return self._userinfo

    @userinfo.setter
    def userinfo(self, input):
        if isinstance(input, Userinfo):
            self._userinfo = input
        else:
            self._userinfo = Userinfo(input)
    
    def __str__(self):
        uri = ''
        
        
        # Append the scheme.
        if self.scheme is not None:
            uri += encode(self.scheme, '+') + ':'
        
        # Append the authority
        has_authority = self._userinfo or self.host is not None or self.port is not None
        if has_authority:
            uri += '//'
            if self._userinfo:
                uri += str(self._userinfo) + '@'
            uri += encode(self.host or '', SUB_DELIMS)
            if self.port is not None:
                uri += ':' + encode(self.port)
        
        # Append the path
        # TODO: Conform this to section 3.3 on the reference.
        if self._path and self._path != ['']:
            path = [encode(x, SUB_DELIMS + '@:') for x in self._path]
            
            # If there is no scheme, we must encode colons in the first chunk.
            # This coresponds to the "path-noscheme" ABNF in section 3.3 of the RFC.
            if not self.scheme and path:
                path[0] = path[0].replace(':', '%%%02x' % ord(':'))
            
            # If there is no authority there can be no empty segments at begining.
            # This coresponds to the "path-absolute" ABNF in section 3.3 of the RFC.
            if not has_authority:
                while path and not path[0]:
                    path.pop(0)
            
            # If there IS an authority we must have a preceding slash.
            # This coresponds to the "path-abempty" ABNF in section 3.3 of the RFC.
            elif path and path[0]:
                path.insert(0, '')
            
            uri += '/'.join(path)
        
        # Append the query.
        if self._query:
            uri += '?' + str(self._query)
        
        # Append the fragment.
        if self.fragment:
            uri += '#' + encode(self.fragment, '/?')
        
        return uri


if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    
    print "Done."
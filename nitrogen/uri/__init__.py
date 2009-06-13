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

Directories:
    >>> uri = URI()
    >>> uri.path = '/abs/path/to/dir/'
    >>> str(uri)
    '/abs/path/to/dir/'

Resolving relative URIs:
    
    >>> base = URI('http://a/b/c/d;p?q')
    >>> def rfc_test(relative, result):
    ...     resolved = base.resolve(relative)
    ...     if str(resolved) != str(result):
    ...         print resolved

Normal examples (from RFC 5.4.1):

	>>> rfc_test("g:h", "g:h")
	>>> rfc_test("g", "http://a/b/c/g")
	>>> rfc_test("./g", "http://a/b/c/g")
	>>> rfc_test("g/", "http://a/b/c/g/")
	>>> rfc_test("/g", "http://a/g")
	>>> rfc_test("//g", "http://g")
	>>> rfc_test("?y", "http://a/b/c/d;p?y")
	>>> rfc_test("g?y", "http://a/b/c/g?y")
	>>> rfc_test("#s", "http://a/b/c/d;p?q#s")
	>>> rfc_test("g#s", "http://a/b/c/g#s")
	>>> rfc_test("g?y#s", "http://a/b/c/g?y#s")
	>>> rfc_test(";x", "http://a/b/c/;x")
	>>> rfc_test("g;x", "http://a/b/c/g;x")
	>>> rfc_test("g;x?y#s", "http://a/b/c/g;x?y#s")
	>>> rfc_test("", "http://a/b/c/d;p?q")
	>>> rfc_test(".", "http://a/b/c/")
	>>> rfc_test("./", "http://a/b/c/")
	>>> rfc_test("..", "http://a/b/")
	>>> rfc_test("../", "http://a/b/")
	>>> rfc_test("../g", "http://a/b/g")
	>>> rfc_test("../..", "http://a/")
	>>> rfc_test("../../", "http://a/")
	>>> rfc_test("../../g", "http://a/g")

Abnormal examples (from RFC 5.4.2):

	>>> # Being careful about having too many '..'s
	>>> rfc_test("../../../g", "http://a/g")
	>>> rfc_test("../../../../g", "http://a/g")

	>>> # Only removes segments that are fully '.' or '..'
	>>> rfc_test("/./g", "http://a/g")
	>>> rfc_test("/../g", "http://a/g")
	>>> rfc_test("g.", "http://a/b/c/g.")
	>>> rfc_test(".g", "http://a/b/c/.g")
	>>> rfc_test("g..", "http://a/b/c/g..")
	>>> rfc_test("..g", "http://a/b/c/..g")

	>>> # Redundant '.'s or '..'s
	>>> rfc_test("./../g", "http://a/b/g")
	>>> rfc_test("./g/.", "http://a/b/c/g/")
	>>> rfc_test("g/./h", "http://a/b/c/g/h")
	>>> rfc_test("g/../h", "http://a/b/c/h")
	>>> rfc_test("g;x=1/./y", "http://a/b/c/g;x=1/y")
	>>> rfc_test("g;x=1/../y", "http://a/b/c/y")

	>>> # Queries and fragments are seperate too!
	>>> rfc_test("g?y/./x", "http://a/b/c/g?y/./x")
	>>> rfc_test("g?y/../x", "http://a/b/c/g?y/../x")
	>>> rfc_test("g#s/./x", "http://a/b/c/g#s/./x")
	>>> rfc_test("g#s/../x", "http://a/b/c/g#s/../x")

	>>> # Schemes overide all!
	>>> rfc_test("http:g", "http:g")
    
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
    
    def has_authority(self):
        return self._userinfo or self.host is not None or self.port is not None
    
    def str(self):
        uri = ''
        
        # Append the scheme.
        if self.scheme is not None:
            uri += encode(self.scheme, '+') + ':'
        
        # Append the authority
        has_authority = self.has_authority()
        if has_authority:
            uri += '//'
            if self._userinfo:
                uri += str(self._userinfo) + '@'
            uri += encode(self.host or '', SUB_DELIMS)
            if self.port is not None:
                uri += ':' + encode(self.port)
        
        # Append the path
        uri += self._path.str(
            scheme=self.scheme is not None,
            authority=has_authority
        )
        
        # Append the query.
        if self._query:
            uri += '?' + str(self._query)
        
        # Append the fragment.
        if self.fragment:
            uri += '#' + encode(self.fragment, '/?')
        
        return uri
    
    __str__ = str
    
    def resolve(self, reference, strict=True):
        # TODO: there may be tons of reference issues here with the userinfo
        # and such being carried from one to another.
        
        # This is coming mainly from RFC section 5.2.2
        R = URI(str(reference))
        T = URI()
        Base = URI(str(self))
        
        # A non-strict parser may ignore a scheme in the reference if it is
        # identical to the base URI's scheme.
        if not strict and R.scheme == Base.scheme:
            R.scheme = None
        
        # If it has a scheme it is essentially absolute already.
        if R.scheme is not None:
            T.scheme = R.scheme
            T.userinfo = R.userinfo
            T.host = R.host
            T.port = R.port
            T.path = R.path
            T.query = R.query
            
        else:
            if R.has_authority():
                T.userinfo = R.userinfo
                T.host = R.host
                T.port = R.port
            else:
                if str(R.path) == '':
                    T.path = Base.path
                    if R.query:
                        T.query = R.query
                    else:
                        T.query = Base.query
                else:
                    if str(R.path).startswith('/'):
                        T.path = R.path
                    else:
                        # TODO MERGE
                        # T.path = merge(Base.path, R.path)
                        if Base.has_authority and str(Base.path) in ('/', ''):
                            T.path = '/' + str(R.path)
                        else:
                            path = str(Base.path)
                            pos = path.rfind('/')
                            if pos > 0:
                                path = path[:pos + 1]
                                T.path = path + str(R.path)
                            else:
                                T.path = R.path
                    T.query = R.query                
                T.userinfo = Base.userinfo
                T.host = Base.host
                T.port = Base.port
            T.scheme = Base.scheme
        
        T.fragment = R.fragment
        # print T.path
        T.path.remove_dot_segments()
        return T
        
        
            
            

if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    
    print "Done."
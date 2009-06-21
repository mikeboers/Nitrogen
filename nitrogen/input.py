# encoding: utf8
"""
Module for WSGI input parsing classes and functions.
"""

import cgi
import collections
    
try:
    from .uri.query import Query
    from .cookie import Container as CookieContainer
except ValueError:
    from uri.query import Query
    from cookie import Container as CookieContainer
        
class _SimpleFields(collections.Mapping):
    """A read-only GET/POST representation.

    Note that this is for general practical use, and are generalized for that
    use case. Therefore, while they will accept more than one value under the same
    key, under normal dict-like usage they will only return the first of those
    values. If the special methods are used to access all of the key/value
    pairs, the order that they were recieved WILL be maintained.
        
    Initialization:
        >>> import StringIO
        >>> post = Post({
        ...     'REQUEST_METHOD': 'POST',
        ...     'wsgi.input': StringIO.StringIO('key=value&same=first&same=second')
        ... })
        >>> post
        [(u'key', u'value'), (u'same', u'first'), (u'same', u'second')]

    Basic usage:
        >>> post['key']
        u'value'

    You cannot modify it:    
        >>> post['key'] = 'new value'
        Traceback (most recent call last):
        ...
        TypeError: 'Post' object does not support item assignment

    Accessing nonexistant data is the same as a dict:
        >>> post['nothere']
        Traceback (most recent call last):
        ...
        KeyError: 'nothere'
        >>> post.get('something') == None
        True

    Lots of normal dict methods:
        >>> post.keys()
        [u'key', u'same']
        >>> post.items()
        [(u'key', u'value'), (u'same', u'first')]

    It will accept more than one of the same key. When accessed by all of the
    normal dict methods, only the first value will ever be returned. You can access
    the rest of them (in order) with the post.list(key) method:

        >>> [(key, post.list(key)) for key in post]
        [(u'key', [u'value']), (u'same', [u'first', u'second'])]

    Alternatively, you can use the allitems() and iterallitems() methods:
        >>> post.allitems()
        [(u'key', u'value'), (u'same', u'first'), (u'same', u'second')]
        >>> type(post.iterallitems())
        <type 'listiterator'>
        >>> for item in post.iterallitems():
        ...     print '%s: %r' % item
        key: u'value'
        same: u'first'
        same: u'second'
    """
    
    def __init__(self, environ):
        self._keys = []
        self._key_i = {}
        self._pairs = []
        for key, value in self._parse_environ(environ):
            if not isinstance(value, unicode):
                value = value.decode('utf8', 'replace')
            if key not in self._key_i:
                self._keys.append(key)
                self._key_i[key] = len(self._pairs)
            self._pairs.append((key, value))
    
    def _parse_environ(self, environ):
        raise NotImplemented()
    
    def __repr__(self):
        return repr(self._pairs)
    
    def __getitem__(self, key):
        return self._pairs[self._key_i[key]][1]
    
    def __iter__(self):
        return iter(self._keys)
    
    def __len__(self):
        return len(self._key_i)
    
    def iter(self, key):
        for k, v in self._pairs:
            if k == key:
                yield v
    
    def list(self, key):
        return list(self.iter(key))
    
    def iterallitems(self):
        return iter(self._pairs)
    
    def allitems(self):
        return self._pairs[:]

class Get(_SimpleFields):
    """Read-only GET parser.
    
    For main examples, see _SimpleFields.
    
    Get initialization:
        
        >>> get = Get({'QUERY_STRING': 'key=value&same=first&same=second'})
        >>> get
        [(u'key', u'value'), (u'same', u'first'), (u'same', u'second')]
    """
    def _parse_environ(self, environ):
        query = environ.get('QUERY_STRING')
        if query is None:
            return []
        query = Query(query)
        return query.iterallitems()

class FileRejectingFieldStorage(cgi.FieldStorage):
    """cgi.FieldStorage class which rejects all posted files.
    """
    def make_file(self, binary=None):
        raise TypeError('Not accepting posting files.')
            
class Post(_SimpleFields):
    """Read-only POST parser.
    
    This class uses a cgi.FieldStorage-like object to do the parsing. The
    class used is located at Post.field_storage_class. The default throws an
    exception on files being posted. To change this, extend the class and
    provide a different FieldStorage-like class which accepts files (returns
    a file handle from a fs.make_file(binary=None) call.
    
    For main examples, see _SimpleFields.
    
    """
    
    field_storage_class = FileRejectingFieldStorage
    
    def _parse_environ(self, environ):
        environ = environ.copy()
        environ['QUERY_STRING'] = ''
        fs = self.field_storage_class(
            fp=environ.get('wsgi.input'),
            environ=environ,
            keep_blank_values=True
        )
        for chunk in fs.list:
            yield (chunk.name.decode('utf8'), chunk.value)

def test_post_unicode():
    """Test to make sure that post is handling unicode properly.
    This only is testing the form-encoded version.
    """
    import StringIO
    post = Post({
        'REQUEST_METHOD': 'POST',
        'wsgi.input': StringIO.StringIO('k%C3%A9y=%C2%A1%E2%84%A2%C2%A3%C2%A2%E2%88%9E%C2%A7%C2%B6%E2%80%A2%C2%AA%C2%BA')
    })
    assert post.keys()[0] == u'kéy'
    assert post.values()[0] == u'¡™£¢∞§¶•ªº'
    
def Cookies(environ):
    return CookieContainer(environ.get('HTTP_COOKIE', ''))

if __name__ == "__main__":
    from test import run
    run()
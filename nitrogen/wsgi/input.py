"""
Module for POST parser.
"""

import cgi
import collections

try:
    from ..uri.query import Query
except ValueError:
    # For local testing.
    import sys
    sys.path.append('..')
    from uri.query import Query
        
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
        [('key', 'value'), ('same', 'first'), ('same', 'second')]

    Basic usage:
        >>> post['key']
        'value'

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
        ['key', 'same']
        >>> post.items()
        [('key', 'value'), ('same', 'first')]

    It will accept more than one of the same key. When accessed by all of the
    normal dict methods, only the first value will ever be returned. You can access
    the rest of them (in order) with the post.list(key) method:

        >>> [(key, post.list(key)) for key in post]
        [('key', ['value']), ('same', ['first', 'second'])]

    Alternatively, you can use the allitems() and iterallitems() methods:
        >>> post.allitems()
        [('key', 'value'), ('same', 'first'), ('same', 'second')]
        >>> type(post.iterallitems())
        <type 'listiterator'>
        >>> for item in post.iterallitems():
        ...     print '%s: %r' % item
        key: 'value'
        same: 'first'
        same: 'second'
    """
    
    def __init__(self, environ):
        self._keys = []
        self._key_i = {}
        self._pairs = []
        for key, value in self._parse_environ(environ):
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
        [('key', 'value'), ('same', 'first'), ('same', 'second')]
    """
    def _parse_environ(self, environ):
        query = environ.get('QUERY_STRING')
        if query is None:
            return
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
            yield (chunk.name, chunk.value)
    
if __name__ == "__main__":
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."
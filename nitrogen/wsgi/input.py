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

class FileRejectingFieldStorage(cgi.FieldStorage):
    """cgi.FieldStorage class which rejects all posted files."""
    def make_file(self, binary=None):
        raise TypeError('Not accepting posting files.')
        
class _SimpleFields(collections.Mapping):
    """A read-only GET/POST representation.

    Note that this is for general practical use, and are generalized for that
    use case. Therefore, while they will accept more than one value under the same
    key, under normal dict-like usage they will only return the first of those
    values. Also, while keys do not retain the order that they were parsed in,
    the different values for each key certainly do.
        
    Initialization:
        >>> import StringIO
        >>> post = Post({
        ...     'REQUEST_METHOD': 'POST',
        ...     'wsgi.input': StringIO.StringIO('key=value&same=first&same=second')
        ... })
        >>> post
        {'key': ['value'], 'same': ['first', 'second']}

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
        <type 'generator'>
        >>> for item in post.iterallitems():
        ...     print '%s: %r' % item
        key: 'value'
        same: 'first'
        same: 'second'
    """
    
    field_storage_class = FileRejectingFieldStorage
    
    def __init__(self, environ):
        self._data = {}
        for key in fs:
            self._data[key] = fs.getlist(key)
    
    def _parse_environ(self, environ):
        raise NotImplemented()
    
    def __repr__(self):
        return repr(self._data)
    
    def __getitem__(self, key):
        return self._data[key][0]
    
    def __iter__(self):
        return iter(self._data)
    
    def __len__(self):
        return len(self._data)
    
    def list(self, key):
        return self._data.get(key)
    
    def iterallitems(self):
        for key in self:
            for value in self.list(key):
                yield (key, value)
    
    def allitems(self):
        return list(self.iterallitems())

class Get(_SimpleFields):
    pass

class Post(_SimpleFields):
    """Read-only POST parser.
    
    This class uses a cgi.FieldStorage-like object to do the parsing. The
    class used is located at Post.field_storage_class. The default throws an
    exception on files being posted. To change this, extend the class and
    provide a different FieldStorage-like class which accepts files (returns
    a file handle from a fs.make_file(binary=None) call.
    
    """
    
    def _parse_environ(self, environ):
        environ = environ.copy()
        environ['QUERY_STRING'] = ''
        fs = self.field_storage_class(
            fp=environ.get('wsgi.input'),
            environ=environ,
            keep_blank_values=True
        )
        for key in fs:
            for value in fs.getlist(key):
                yield (key, value)
    
if __name__ == "__main__":
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."
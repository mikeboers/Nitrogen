"""

A set of read-only GET/POST parsers.
    
Initialization:
    >>> get = Get({'QUERY_STRING': 'key=value&same=first&same=second'})

Basic usage:
    >>> get['key']
    'value'

You cannot modify it:    
    >>> get['key'] = 'new value'
    Traceback (most recent call last):
    ...
    TypeError: 'Get' object does not support item assignment

Accessing nonexistant data is the same as a dict:
    >>> get['nothere']
    Traceback (most recent call last):
    ...
    KeyError: 'nothere'
    >>> get.get('something') == None
    True

Lots of normal dict methods:
    >>> get.keys()
    ['key', 'same']
    >>> get.items()
    [('key', 'value'), ('same', 'first')]

It will accept more than one of the same key. When accessed by all of the
normal dict methods, only the first value will ever be returnd. You can access
the rest of them with the Get.list(key) method:

    >>> [(key, get.list(key)) for key in get]
    [('key', ['value']), ('same', ['first', 'second'])]

POST Initialization:
    >>> import StringIO
    >>> post = Post({
    ...     'REQUEST_METHOD': 'POST',
    ...     'wsgi.input': StringIO.StringIO('key=value&same=first&same=second')
    ... })
    >>> post
    {'key': ['value'], 'same': ['first', 'second']}

"""

import cgi
import collections

class SimpleFields(collections.Mapping):
    
    def __init__(self, environ):
        self._data = {}            
        fs = self._fieldstorage(environ)
        for key in fs:
            self._data[key] = fs.getlist(key)
    
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

class _FieldStorage(cgi.FieldStorage):
    def make_file(self, binary=None):
        raise TypeError('Not accepting posting files.')

class Get(SimpleFields):
    def _fieldstorage(self, environ):
        return _FieldStorage(
            fp=None,
            environ={'QUERY_STRING': environ.get('QUERY_STRING', '')},
            keep_blank_values=True
        )

class Post(SimpleFields):
    def _fieldstorage(self, environ):
        environ = environ.copy()
        environ['QUERY_STRING'] = ''
        return _FieldStorage(
            fp=environ.get('wsgi.input'),
            environ=environ,
            keep_blank_values=True
        )

if __name__ == "__main__":
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."
"""Module for middlewear that will parse GET, POST, posted files, and basic cookies."""

import cgi
import collections
    
try:
    from ..uri.query import Query
    from ..cookie import Container as CookieContainer
except ValueError:
    import sys
    sys.path.insert(0, '..')
    from uri.query import Query
    from cookie import Container as CookieContainer

class ReadOnlyMapping(collections.Mapping):
  
    def __init__(self, supplier=None):
        self.supplier = supplier
        self._is_setup = False

    def _setup(self):    
        self._is_setup = True
        self.__pairs = []
        self.__keys = []
        self.__key_i = {}
        for key, value in self.supplier():
            if key not in self.__key_i:
                self.__keys.append(key)
                self.__key_i[key] = len(self.__pairs)
            self.__pairs.append((key, value))
        self.supplier = None
    
    @property
    def _pairs(self):
        if not self._is_setup:
            self._setup()
        return self.__pairs
        
    @property
    def _keys(self):
        if not self._is_setup:
            self._setup()
        return self.__keys
        
    @property
    def _key_i(self):
        if not self._is_setup:
            self._setup()
        return self.__key_i
    
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

def PostStorage(environ, accept, make_file, max_size):
    class FieldStorage(cgi.FieldStorage):    
        def make_file(self, binary=None):
            return cgi.FieldStorage.make_file(self, binary)
    environ = environ.copy()
    environ['QUERY_STRING'] = ''
    return FieldStorage(
        fp=environ.get('wsgi.input'),
        environ=environ,
        keep_blank_values=True
    )

def input_parser(app, accept=False, make_file=None, max_size=None):
    def inner(environ, start):
        
        # Build the get object
        query = environ.get('QUERY_STRING', '')
        query = Query(query)
        environ['nitrogen.get'] = ReadOnlyMapping(query.iterallitems)
        
        # Post and files.
        post  = environ['nitrogen.post']  = ReadOnlyMapping()
        files = environ['nitrogen.files'] = ReadOnlyMapping()
        
        state = {
            'fs': None
        }
        def builder_builder(is_files):
            def inner():
                if not state['fs']:
                    state['fs'] = PostStorage(
                        environ=environ,
                        accept=files.accept,
                        make_file=files.make_file,
                        max_size=files.max_size
                    )
                for chunk in state['fs'].list:
                    if chunk.filename and is_files:
                        # Send to files object.
                        yield (chunk.name.decode('utf8'), chunk.file)
                    else:
                        # Send to post object.
                        yield (chunk.name.decode('utf8'), chunk.value)
            return inner
        
        files.accept = accept
        files.make_file = make_file
        files.max_size = max_size
        
        post.supplier = builder_builder(False)
        files.supplier = builder_builder(True)
        
        return app(environ, start)
    
    return inner


def test_ReadOnlyMapping_1():
    def gen():
        for x in xrange(10):
            yield x, x**2
    map = ReadOnlyMapping(gen)
    assert map.keys() == range(10)
    assert map.values() == [x**2 for x in range(10)]

def test_get():
    def app(environ, start):
        start('200 OK', [])
        yield "START|"
        for k, v in environ.get('nitrogen.get').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = input_parser(app)
    status, headers, output = WSGIServer(app).run()
    assert output == 'START|END'
    
    status, headers, output = WSGIServer(app).run(QUERY_STRING='key=value&key2=value2')
    assert output == 'START|key=value|key2=value2|END'

def test_post():
    def app(environ, start):
        start('200 OK', [])
        yield "START|"
        for k, v in environ.get('nitrogen.post').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = input_parser(app)
    status, headers, output = WSGIServer(app).run(REQUEST_METHOD='POST')
    assert output == 'START|END'
    
    status, headers, output = WSGIServer(app,
        input='key=value&same=first&same=second').run(REQUEST_METHOD='POST')
    assert output == 'START|key=value|same=first|same=second|END'
        
        
if __name__ == '__main__':
    from test import run, WSGIServer
    run()
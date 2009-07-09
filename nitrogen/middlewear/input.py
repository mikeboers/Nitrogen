"""Web input parsing functions.

The functions and middlewear in this module are designed to parse query string
(GET) and posted data/files. They do so in a lazy manner, only parsing the
input when they must. This gives a little bit of time to setup some
configuration on how the files are parsed.

By default, files are rejected; an exception is thrown when a file is posted.
You can change the accept parameter on the files object to turn off this
behavior. Then, by default, temporary files will be created that will be
removed from the drive as soon as they are garbage collected.

The default temp files will also respond to a max_size attribute on the files
object. They will not accept any more data than the number of bytes specified
on the max_size attribute.

If you want even more control over the files, you can specify a make_file
attribute on the files object, which will be called with keyword arguments
"key" (the key it will have in the files dict), "filename" (as reported by the
browser), and "length" (the content-length of the file as reported by the
browser). It is expected to return a file-like object.

I don't do anything to deal with possibly incomplete files. You will need to
implement your own make_file which returns an object that tracks the written
amount and compares it to the reported content-length.

Notes from cgi.FieldStorage:
	fs.length is the reported content length
		will be -1 if the content length is not given
	fs.file will have the file object
		it could be a stringIO
	fs.name is the field name
	fs.type_options has the type options (it is a dict)
		maybe it has a charset key? =]
	it has internal protection for recieving too much in the read_binary mode, but that is only triggered from read_single (when there is a length), which is triggerd when the content type is not multipart/* or application/x-www-form-urlencoded. If it is multipart, then a bunch of FieldStorages are made from the multiple parts and those are finally read with read_single
		so if a length is provided, then it already stops reading after that far
		if there is no length, it reads until the boundary or the end of file.

"""

import cgi
import collections
import sys
import tempfile

if __name__ == '__main__':
    sys.path.append('../..')
    import nitrogen.middlewear as junk
    __package__ = 'nitrogen.middlewear'

from ..uri.query import Query
from .. import cookie

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






class DefaultFile(object):
    def __init__(self, max_size):
        self.fh = tempfile.TemporaryFile("w+b")
        self.max_size = max_size
        self.written = 0
        
        # Transfer all the methods.
        for attr in 'read flush seek tell fileno'.split():
            setattr(self, attr, getattr(self.fh, attr))
    
    def write(self, stuff):
        self.written += len(stuff)
        if self.max_size and self.max_size < self.written:
            raise ValueError("Too much written to file!")
        return self.fh.write(stuff)


def PostStorage(environ, accept, make_file, max_size):
    class FieldStorage(cgi.FieldStorage):    
        def make_file(self, binary=None):
            if not accept:
                raise ValueError("Not accepting posted files.")
            if make_file:
                return make_file(
                    key=self.name,
                    filename=self.filename,
                    length=(self.length if self.length > 0 else 0)
                )
            if self.length > max_size:
                raise ValueError("Reported file size is too big.")
            return DefaultFile(max_size=max_size)
    environ = environ.copy()
    environ['QUERY_STRING'] = ''
    fs = FieldStorage(
        fp=environ.get('wsgi.input'),
        environ=environ,
        keep_blank_values=True
    )
    
    # Assert that all the files have been written out.
    for chunk in fs.list:
        if chunk.filename and hasattr(chunk.file, 'getvalue'): # IT is a stringIO
            contents = chunk.file.getvalue()
            chunk.file = chunk.make_file(None)
            chunk.file.write(contents)
            chunk.file.seek(0)
    return fs

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
                    # sys.stderr.write(str(chunk.filename) + '\n')
                    if chunk.filename and is_files:
                        # Send to files object.
                        yield (chunk.name.decode('utf8', 'replace'), chunk.file)
                    elif not chunk.filename and not is_files:
                        # Send to post object.
                        yield (chunk.name.decode('utf8', 'replace'), chunk.value.decode('utf8', 'replace'))
            return inner
        
        files.accept = accept
        files.make_file = make_file
        files.max_size = max_size
        
        post.supplier = builder_builder(False)
        files.supplier = builder_builder(True)
        
        return app(environ, start)
    
    return inner

def cookie_parser(app, hmac_key=None):
    class_ = cookie.make_signed_container(hmac_key) if hmac_key else cookie.Container
    def inner(environ, start):
        environ['nitrogen.cookies'] = class_(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return inner

def cookie_builder(app, strict=True):
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.headers = None

        def inner_start(self, status, headers):
            cookies = self.environ.get('nitrogen.cookies')
            if cookies:
                self.headers = cookies.build_headers()
                headers.extend(self.headers)
            self.start(status, headers)

        def __iter__(self):    
            for x in app(self.environ, self.inner_start):
                yield x
            if not strict:
                return
            cookies = self.environ.get('nitrogen.cookies')
            if cookies is None:
                raise ValueError('Cookies have been removed from environ.')
            headers = cookies.build_headers()
            if self.headers is not None and self.headers != headers:
                raise ValueError('Cookies have been modified since WSGI start.', self.headers, headers)
    return inner

def full_parser(app, hmac_key=None, strict=True):
    return cookie_builder(
        input_parser(cookie_parser(app, hmac_key=hmac_key)),
        strict=strict
    )

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
    from nitrogen.test import run, WSGIServer
    run()
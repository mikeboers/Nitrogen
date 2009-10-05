"""Web input parsing functions.

The functions and middleware in this module are designed to parse query string
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

if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import cgi
import collections
import sys
import tempfile
import logging

from . import cookie
from .uri import URI
from .uri.query import Query
from .multimap import MultiMap, DelayedMultiMap
from .headers import DelayedHeaders

class DefaultFile(object):
    """Class for file uploads in default state."""
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


def build_raw_field_storage(environ, accept_files, make_file, max_file_size):
    class FieldStorage(cgi.FieldStorage):    
        def make_file(self, binary=None):
            if not accept_files:
                raise ValueError("Not accepting posted files.")
            if make_file:
                return make_file(
                    key=self.name,
                    filename=self.filename,
                    length=(self.length if self.length > 0 else 0)
                )
            if self.length > max_file_size:
                raise ValueError("Reported file size is too big.")
            return DefaultFile(max_size=max_file_size)
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

def get_parser(app, **kwargs):
    """WSGI middleware which parses the query string.
    
    A read-only MultiMap is stored on the environment at 'nitrogen.get'.
    
    """
    
    def inner(environ, start):
        def gen():
            query = environ.get('QUERY_STRING', '')
            return Query(query).allitems()
        environ['nitrogen.get'] = DelayedMultiMap(gen)
        return app(environ, start)
    return inner    
    
def post_parser(app, accept_files=False, make_file=None, max_file_size=None, environ=None, **kwargs):
    """WSGI middleware which parses posted data.
    
    Lazy-evaluation gives you enough time to specify the accept_files, make_file,
    and max_file_size as attributes of the files object.
    
    Adds 'nitrogen.post' and 'nitrogen.files' to the environ.
    
    Params:
        app - The WSGI app to wrap.
        accept_files - Boolean if files should be accepted or not.
        make_file - Callback that returns a file-like object to recieve data.
        max_file_size - Maximum acepted file size for default file reciever.
    
    make_file:
        If None, a default file object will be used (object of DefaultFile)
        which uses the tempfile module to make a temporary file.
        
        If not None, it must be a callable object which takes key, filename,
        and length as keyword arguments, and returns an object with
    
    """
    
    def inner(environ, start):
        
        # Post and files.
        post  = environ['nitrogen.post']  = DelayedMultiMap()
        files = environ['nitrogen.files'] = DelayedMultiMap()
        
        def map_supplier_builder(is_files):
            def inner():
                fs = map_supplier_builder.fs
                if not fs:
                    fs = map_supplier_builder.fs = build_raw_field_storage(
                        environ=environ,
                        accept_files=files.accept_files,
                        make_file=files.make_file,
                        max_file_size=files.max_file_size
                    )
                for chunk in fs.list:
                    # sys.stderr.write(str(chunk.filename) + '\n')
                    if chunk.filename and is_files:
                        # Send to files object.
                        yield (chunk.name.decode('utf8', 'replace'), chunk.file)
                    elif not chunk.filename and not is_files:
                        # Send to post object.
                        yield (chunk.name.decode('utf8', 'replace'), chunk.value.decode('utf8', 'replace'))
            return inner
        map_supplier_builder.fs = None
        
        files.accept_files = accept_files
        files.make_file = make_file
        files.max_file_size = max_file_size
        
        post.supplier = map_supplier_builder(is_files=False)
        files.supplier = map_supplier_builder(is_files=True)
        
        return app(environ, start)
    
    return inner
        

def cookie_parser(app, hmac_key=None, **kwargs):
    """WSGI middleware which parses incoming cookies and places them into a
    standard cookie container keyed under 'nitrogen.cookies'.
    
    Params:
        app - The WSGI app to wrap.
        hmac_key - If provided cookies will be signed on output, and the
            signatures verified on import.
    """
    
    class_ = cookie.make_signed_container(hmac_key) if hmac_key else cookie.Container
    def inner(environ, start):
        environ['nitrogen.cookies'] = class_(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return inner


def cookie_builder(app, **kwargs):
    """WSGI middleware which sends Set-Cookie headers as nessesary so that the
    client's cookies will resemble the cookie container stored in the environ
    at 'nitrogen.cookies'.
    
    This tends to be used along with the cookie_parser.
    """
    def inner(environ, start):
        def inner_start(status, headers):
            cookies = self.environ['nitrogen.cookies']
            headers.extend(cookies.build_headers())
            start(status, headers)
        return app(environ, start)
    return inner
    
def uri_parser(app, **kwargs):
    """WSGI middleware which adds a URI object into the environment.
    
    This thing is mutable... Watch out!
    
    """
    
    def inner(environ, start):
        environ['nitrogen.uri'] = URI('http://' + environ['SERVER_NAME'] + environ.get('REQUEST_URI', ''))
        return app(environ, start)
    return inner

def header_parser(app, **kwargs):
    def inner(environ, start):
        def gen():
            for k, v in environ.items():
                if k.startswith('HTTP_'):
                    yield k[5:], v
        environ['nitrogen.headers'] = DelayedHeaders(gen)
        return app(environ, start)
    return inner
        
def request_params(app, parse_uri=True, parse_get=True, parse_post=True,
        parse_cookie=True, build_cookie=True, parse_headers=True, **kwargs):
    if parse_headers:
        app = header_parser(app, **kwargs)
    if parse_uri:
        app = uri_parser(app, **kwargs)
    if parse_get:
        app = get_parser(app, **kwargs)
    if parse_post:
        app = post_parser(app, **kwargs)
    if parse_cookie:
        app = cookie_parser(app, **kwargs)
    if build_cookie:
        app = cookie_builder(app, **kwargs)
    return app


def test_DelayedMultiMap_1():
    def gen():
        for x in xrange(10):
            yield x, x**2
    map = DelayedMultiMap(gen)
    assert map.keys() == range(10)
    assert map.values() == [x**2 for x in range(10)]

def test_get():
    import webtest
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "START|"
        for k, v in environ.get('nitrogen.get').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = request_params(app)
    app = webtest.TestApp(app)
    
    res = app.get('/')
    assert res.body == 'START|END'
    
    res = app.get('/?key=value&key2=value2')
    assert res.body == 'START|key=value|key2=value2|END'

def test_post():
    import webtest
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "START|"
        for k, v in environ.get('nitrogen.post').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = request_params(app)
    app = webtest.TestApp(app)
    
    res = app.post('/')
    assert res.body == 'START|END'
    
    res = app.post('/', 'key=value&same=first&same=second')
    assert res.body == 'START|key=value|same=first|same=second|END'
        
        
if __name__ == '__main__':
    from nitrogen.test import run
    run()
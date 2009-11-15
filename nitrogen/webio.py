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

from cStringIO import StringIO

from . import cookie
from .uri import URI
from .uri.query import Query
from .multimap import MultiMap, DelayedMultiMap
from .headers import DelayedHeaders


log = logging.getLogger(__name__)


class MaxLengthWrapper(object):
    
    """Wrapper around file-like objects to ensure that they only recieve as
    much data as we have permitted them to.

    """
    
    def __init__(self, fh, max_length):
        self.fh = fh
        self.max_length = max_length
        self.recieved = 0
        self.seek = fh.seek
    
    def write(self, stuff):
        self.recieved += len(stuff)
        if self.max_length is not None and self.recieved > self.max_length:
            raise ValueError("too much data recieved")
        return self.fh.write(stuff)


def make_stringio(key, filename, length):
    """Simple make_file which returns a StringIO."""
    return StringIO()


def make_temp_file(key, filename, length):
    """Simple make_file which returns a temporary file.
    
    The underlaying file will be removed from the disk when this object is
    garbage collected. See the tempfile module.
    
    """
    
    return tempfile.TemporaryFile("w+b") # We do need the "+" in there...
    # old: TempFile(max_length=length)




def field_storage(environ, make_file, max_file_length):
    """Build the FieldStorage that we pull the post and file data from.
    
    We need to define two FieldStorage classes here: one master for driving
    the parsing of the request, and one child for representing the individual
    parameters (but only used for files as the base uses a MiniFieldStorage
    class for straight key/value pairs).
    
    In the master, we overload the read_single method to raise an error if
    there is any data present. This is because we expect the read_single to
    never be called in normal usage. Depending on the content type of the
    request, either read_urlencoded (for "application/x-www-form-urlencoded"),
    read_multi (for "multipart/*"), or read_single (anything else) is called.
    For the master we are clearly expecting only read_urlencoded or read_multi
    to be called. However, when making a POST with an empty string or empty
    object from jQuery, the content type is set to "text/plain" and no data
    is actually sent. This was tricking this system into making files and
    requiring a make_file function to be set even though no data will be
    recieved.
    
    In the child, we overload the make_file function to make sure that we are
    able to make files, make sure they are not too long (both by checking the
    posted content length and wrapping the files in a MaxLengthWrapper
    object), and handle the calling of the make_file function.
    
    """
    
    class ChildFieldStorage(cgi.FieldStorage):
        
        def __init__(self, *args, **kwargs):
            cgi.FieldStorage.__init__(self, *args, **kwargs)
            self.made_file = False
            
        def make_file(self, binary=None):
            self.made_file = True
            if not make_file:
                raise ValueError("not accepting posted files; "
                    "no make_file set")
            if max_file_length is not None and self.length > max_file_length:
                raise ValueError("reported file size is too big: %r > %r" % (
                    self.length, max_file_length))
            return MaxLengthWrapper(make_file(
                self.name,
                self.filename,
                self.length if self.length > 0 else 0
            ), max_file_length)
    
    class MasterFieldStorage(cgi.FieldStorage):
        
        FieldStorageClass = ChildFieldStorage
        
        def read_single(self):
            if self.length == 0:
                return
            if self.length > 0:
                raise ValueError("we don't understand %r content-type" %
                    self.type)
            if self.fp.read(1):
                raise ValueError("we don't understand %r content-type" %
                    self.type)
            return
    
    environ = environ.copy()
    environ['QUERY_STRING'] = ''
    fs = MasterFieldStorage(
        fp=environ.get('wsgi.input'),
        environ=environ,
        keep_blank_values=True
    )
    
    
    # The list isn't always there. Try to post a empty string with
    # jQuery and it sends content-type "text/plain", so fs.list will be None.
    fs.list = fs.list or []
    
    # Assert that no more StringIO objects (from the FieldStorage) are left
    # and that all the files have been written out through the make_file.
    for chunk in fs.list:
        
        # Using an attribute I added to FieldStorage to see if the internal
        # StringIO is still in use.
        if chunk.filename and not chunk.made_file:
            contents = chunk.file.getvalue()
            chunk.file = chunk.make_file()
            chunk.file.write(contents)
            chunk.file.seek(0)
        
        # Pull the actual files out of the MaxLengthWrapper(s).
        if chunk.filename:
            chunk.file = chunk.file.fh
    
    return fs


def get_parser(app, **kwargs):
    """WSGI middleware which parses the query string.
    
    A read-only DelayedMultiMap is stored on the environment at 'nitrogen.get'.
    
    """
    
    def inner(environ, start):
        def gen():
            query = environ.get('QUERY_STRING', '')
            return Query(query).allitems()
        environ['nitrogen.get'] = DelayedMultiMap(gen)
        return app(environ, start)
    return inner    


def post_parser(app, make_file=None, max_file_length=None, environ=None, **kwargs):
    """WSGI middleware which parses posted data.
    
    Lazy-evaluation via DelayedMultiMap(s) gives you enough time to specify
    the make_file, and max_file_length as attributes of the files object.
    
    Adds 'nitrogen.post' and 'nitrogen.files' to the environ. If the request
    is not a POST, then empty MultiMaps will be inserted instead. The files
    mapping will still have the default make_file and max_file_length, but it
    will not do anything with them.
    
    Params:
        app - The WSGI app to wrap.
        make_file - None, or a callback that returns a file-like object to
            recieve data.
        max_file_length - Maximum amount of data to recieve for any file.
    
    make_file:
        If None, files will not be accepted. Otherwise it must be a callable
        object which takes key, filename, and length as posotional arguments,
        and returns an object with a write method.
    
    """
    
    def inner(environ, start):
        
        # Don't need to bother doing anything fancy if it isn't a POST.
        if environ['REQUEST_METHOD'].lower() != 'post':
            post  = MultiMap()
            files = MultiMap()
        
        else:
            def map_supplier_builder(is_files):
                def supplier():
                    fs = map_supplier_builder.fs
                    if not fs:
                        fs = map_supplier_builder.fs = field_storage(
                            environ=environ,
                            make_file=files.make_file,
                            max_file_length=files.max_file_length
                        )
                    for chunk in fs.list:
                        charset = fs.type_options.get('charset', 'utf8')
                        # Send to files object?
                        if chunk.filename and is_files:
                            yield (chunk.name.decode(charset, 'error'), chunk.file)
                        # Send to post object?
                        elif not chunk.filename and not is_files:
                            yield (chunk.name.decode(charset, 'error'), chunk.value.decode(charset, 'error'))
                return supplier
            map_supplier_builder.fs = None
            
            post  = DelayedMultiMap(map_supplier_builder(is_files=False))
            files = DelayedMultiMap(map_supplier_builder(is_files=True))
            
        files.make_file = make_file
        files.max_file_length = max_file_length
        
        environ['nitrogen.post'] = post
        environ['nitrogen.files'] = files
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
            cookies = environ['nitrogen.cookies']
            log.debug('setting cookies: %r' % cookies)
            headers.extend(cookies.build_headers())
            start(status, headers)
        return app(environ, inner_start)
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
    

def request_params(app, parse_headers=True, parse_uri=True, parse_get=True, parse_post=True,
        parse_cookie=True, build_cookie=True, **kwargs):
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
"""Web input parsing functions.

The functions and middleware in this module are designed to parse query string
(GET) and posted data/files. They do so in a lazy manner, only parsing the
input when they must. This gives a little bit of time to setup some
configuration on how the files are parsed.

By default, files are rejected; an exception is thrown when a file is posted.
If you want to accept files you must specify a make_file attribute on the
files object, which will be called with positional arguments `key` (the key it
will have in the files dict), `filename` (as reported by the browser), and
`length` (the content-length of the file as reported by the browser; may be
None). It is expected to return a file-like object.

There are two make_file functions provided: make_stringio and make_temp_file.

The file-like object returned from make_file is wrapped in a class which makes
sure that it only accepts as much data as we allow via the
`max_file_length` attribute. There is protection elsewhere to make sure that
the client reported length is smaller than the `max_file_length` but the client
need not provide it.

"""


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
    """Wrapper around file-like objects to ensure that they recieve as much
    data as we have permitted them to.

    """
    
    def __init__(self, fh, max_length):
        self.fh = fh
        self.max_length = max_length
        self.recieved = 0
        self.seek = fh.seek
    
    def write(self, stuff):
        self.recieved += len(stuff)
        if self.max_length is not None and self.recieved > self.max_length:
            raise ValueError("too much data recieved; got %d" % self.recieved)
        return self.fh.write(stuff)


def make_stringio(field):
    """Simple make_file which returns a StringIO."""
    return StringIO()


def make_temp_file(field):
    """Simple make_file which returns a temporary file.
    
    The underlaying file will be removed from the disk when this object is
    garbage collected. See the tempfile module.
    
    """
    
    return tempfile.TemporaryFile("w+b") # We do need the "+" in there...




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
        
        @property
        def key(self):
            return self.name
            
        def make_file(self, binary=None):
            self.made_file = True
            if not make_file:
                raise ValueError("no make_file set; "
                    "not accepting posted files")
            if max_file_length is not None and self.length > max_file_length:
                raise ValueError("reported file size is too big: %r > %r" % (
                    self.length, max_file_length))
            return MaxLengthWrapper(make_file(self), max_file_length)
    
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
            if chunk.length >= 0 and chunk.file.recieved != chunk.length:
                raise ValueError("incorrect file length; got %d of %d" % (
                    chunk.file.recieved, chunk.length))
            chunk.file = chunk.file.fh
    
    return fs


def get_parser(app, **kwargs):
    """WSGI middleware which parses the query string.
    
    A read-only DelayedMultiMap is stored on the environment at 'nitrogen.get'.
    
    """
    
    def get_parser_app(environ, start):
        def gen():
            query = environ.get('QUERY_STRING', '')
            return Query(query).allitems()
        environ['nitrogen.get'] = DelayedMultiMap(gen)
        return app(environ, start)
    return get_parser_app    


def post_parser(app, make_file=None, max_file_length=None, environ=None, **kwargs):
    """WSGI middleware which parses posted data.
    
    Lazy-evaluation via DelayedMultiMap(s) gives you enough time to specify
    the `make_file`, and `max_file_length` as attributes of the files object.
    
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
    
    def post_parser_app(environ, start):
        
        # Don't need to bother doing anything fancy if this is a GET
        if environ['REQUEST_METHOD'].lower() == 'get':
            post  = MultiMap()
            files = MultiMap()
        
        else:
            def post_parser_supplier_builder(is_files):
                def post_parser_supplier():
                    fs = post_parser_supplier_builder.fs
                    if not fs:
                        fs = post_parser_supplier_builder.fs = field_storage(
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
                return post_parser_supplier
            post_parser_supplier_builder.fs = None
            
            post  = DelayedMultiMap(post_parser_supplier_builder(is_files=False))
            files = DelayedMultiMap(post_parser_supplier_builder(is_files=True))
            
        files.make_file = make_file
        files.max_file_length = max_file_length
        
        environ['nitrogen.post'] = post
        environ['nitrogen.files'] = files
        return app(environ, start)
    
    return post_parser_app
        

def cookie_parser(app, hmac_key=None, **kwargs):
    """WSGI middleware which parses incoming cookies and places them into a
    standard cookie container keyed under 'nitrogen.cookies'.
    
    Params:
        app - The WSGI app to wrap.
        hmac_key - If provided cookies will be signed on output, and the
            signatures verified on import.
    """
    
    class_ = cookie.make_signed_container(hmac_key) if hmac_key else cookie.Container
    def cookie_parser_app(environ, start):
        environ['nitrogen.cookies'] = class_(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return cookie_parser_app


def cookie_builder(app, **kwargs):
    """WSGI middleware which sends Set-Cookie headers as nessesary so that the
    client's cookies will resemble the cookie container stored in the environ
    at 'nitrogen.cookies'.
    
    This tends to be used along with the cookie_parser.
    """
    def cookie_builder_app(environ, start):
        def cookie_builder_start(status, headers, exc_info=None):
            cookies = environ['nitrogen.cookies']
            headers.extend(cookies.build_headers())
            start(status, headers)
        return app(environ, cookie_builder_start)
    return cookie_builder_app


def uri_parser(app, **kwargs):
    """WSGI middleware which adds a URI object into the environment.
    
    This thing is mutable... Watch out!
    
    """
    
    def uri_parser_app(environ, start):
        environ['nitrogen.uri'] = URI('http://' + environ['SERVER_NAME'] + environ.get('REQUEST_URI', ''))
        return app(environ, start)
    return uri_parser_app


def header_parser(app, **kwargs):
    """WSGI middleware which adds a header mapping to the environment."""
    def header_parser_app(environ, start):
        def gen():
            for k, v in environ.items():
                if k.startswith('HTTP_'):
                    yield k[5:], v
        environ['nitrogen.headers'] = DelayedHeaders(gen)
        return app(environ, start)
    return header_parser_app
    

def request_params(app, parse_headers=True, parse_uri=True, parse_get=True, parse_post=True,
        parse_cookies=True, build_cookies=True, **kwargs):
    if parse_headers:
        app = header_parser(app, **kwargs)
    if parse_uri:
        app = uri_parser(app, **kwargs)
    if parse_get:
        app = get_parser(app, **kwargs)
    if parse_post:
        app = post_parser(app, **kwargs)
    if parse_cookies:
        app = cookie_parser(app, **kwargs)
    if build_cookies:
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
    from .test import run
    run()
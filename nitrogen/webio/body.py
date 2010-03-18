
from cStringIO import StringIO
import cgi
import weakref

from multimap import MultiMap


ENVIRON_BODY_CACHE_KEY = 'nitrogen.body_cache'
ENVIRON_POST_KEY = 'nitrogen.post'
ENVIRON_FILES_KEY = 'nitrogen.files'


def assert_body_cache(environ, environ_key=None):
    environ_key = environ_key or ENVIRON_BODY_CACHE_KEY
    if environ_key not in environ:
        stdin = environ['wsgi.input']
        cache = StringIO(stdin.read())
        cache.seek(0)
        environ['wsgi.input'] = environ[environ_key] = cache

def get_body_file(environ, environ_key=None):
    assert_body_cache(environ, environ_key)
    return environ[environ_key]

def get_body(environ, environ_key=None):
    file = get_body_file(environ, environ_key)
    tell = file.tell()
    body = file.read()
    file.seek(tell)
    return body






class MaxLengthWrapper(object):
    """Wrapper around file-like objects to ensure that they recieve only as
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
    # We do need the "+" in there for the tempfile module's sake.
    import tempfile
    return tempfile.TemporaryFile("w+b")








class SingleField(cgi.FieldStorage):

    def __init__(self, parent, *args, **kwargs):
        self.parent = wekref.proxy(parent)
        self.made_file = False
        cgi.FieldStorage.__init__(self, *args, **kwargs)

    @property
    def key(self):
        return self.name

    def make_file(self, binary=None):
        self.made_file = True
        max_file_length = self.parent.max_file_length
        if max_file_length is not None and self.length > max_file_length:
            raise ValueError("reported file size is too big: %r > %r" % (
                self.length, max_file_length))
        return MaxLengthWrapper(self.parent.make_file(self), max_file_length)


class FieldStorage(cgi.FieldStorage):
    
    def __init__(self, environ, make_file=None, max_length=None, keep_blank_values=True):
        if make_file is not None:
            self.make_file = make_file
        self.max_length = max_length
        environ = environ.copy()
        environ['QUERY_STRING'] = ''
        cgi.FieldStorage.__init__(self, 
            fp=environ['wsgi.input'],
            environ=environ,
            keep_blank_values=keep_blank_values
        )
            
    def FieldStorageClass(self, *args, **kwargs):
        return SingleField(self, *args, **kwargs)
    
    def read_single(self):
        # We don't support non url encoded or mime type forms. But we must
        # take special care to make sure something was actually sent before
        # erroring, because jQuery (and others) change the Content-Type to
        # text/plain if the ajax post has no content.
        if self.length == 0:
            return
        if self.length > 0:
            raise ValueError("we don't understand %r content-type" %
                self.type)
        if self.fp.read(1):
            raise ValueError("we don't understand %r content-type" %
                self.type)
        return
    
    def make_file(self, field):
        """Create the file object for the given field to write into.
        
        This is given a SingleField object (which extends cgi.FieldStorage)
        and must return a file-like object to store the contents.
        
        Defaults to raising a ValueError to stop all posted files.
        
        """
        raise ValueError("no make_file set; not accepting posted files")





def parse_body(environ, make_file=None, max_file_length=None, cache_body=True,
        post_key=None, files_key=None, body_cache_key=None
    ):
    
    post_key = post_key or ENVIRON_POST_KEY
    files_key = files_key or ENVIRON_FILES_KEY
    
    # Don't need to bother doing anything fancy if this is a GET
    if environ['REQUEST_METHOD'].lower() in ('get', 'head'):
        return MultiMap(), MultiMap()
    
    # Don't need to bother reparsing if we have already cached it.
    if post_key in environ and files_key in environ:
        return environ[post_key], environ[files_key]
    
    if cache_body:
        assert_body_cache(environ, environ_key=body_cache_key)
    
    make_file = make_file or environ.get('nitrogen.body.make_file')
    max_file_length = max_file_length or environ.get('nitrogen.max_file_length.make_file')
    fs = FieldStorage(
        environ=environ,
        make_file=make_file,
        max_file_length=max_file_length
    )
    
    post, files = MultiMap(), MultiMap()
    
    # The list isn't always there. Try to post a empty string with
    # jQuery and it sends content-type "text/plain", so fs.list will be None.
    for chunk in fs.list or []:
        charset = fs.type_options.get('charset', 'utf8')
        if chunk.filename:
            # Using an attribute I added to FieldStorage to see if the internal
            # StringIO is still in use.
            if not chunk.made_file:
                contents = chunk.file.getvalue()
                chunk.file = chunk.make_file()
                chunk.file.write(contents)
                chunk.file.seek(0)
            # Pull the actual files out of the MaxLengthWrapper(s).
            if chunk.length >= 0 and chunk.file.recieved != chunk.length:
                raise ValueError("incorrect file length; got %d of %d" % (
                    chunk.file.recieved, chunk.length))
            file = chunk.file.fh
            files.append((chunk.name.decode(charset, 'error'), file))
        else:
            post.append((chunk.name.decode(charset, 'error'), chunk.value.decode(charset, 'error')))
    
    environ[post_key] = post
    environ[files_key] = files
    
    return post, files


def parse_post(*args, **kwargs):
    return parse_body(*args, **kwargs)[0]
    
    
def parse_files(*args, **kwargs):
    return parse_body(*args, **kwargs)[0]



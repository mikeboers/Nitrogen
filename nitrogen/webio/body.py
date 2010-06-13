
from cStringIO import StringIO
import cStringIO as cstringio
import StringIO as stringio
import io
import cgi
import weakref

import werkzeug as wz

from multimap import MutableMultiMap



def assert_body_cache(environ):
    stdin = environ['wsgi.input']
    # The OutputType here is just me being paranoid. Likely not nessesary.
    if not isinstance(stdin, (cstringio.InputType, io.StringIO, stringio.StringIO, cstringio.OutputType)):
        cache = StringIO(stdin.read())
        cache.seek(0)
        environ['wsgi.input'] = cache


def get_body_cache(environ):
    assert_body_cache(environ)
    return environ['wsgi.input']


def rewind_body_cache(environ):
    get_body_cache(environ).seek(0)


def get_body(environ):
    file = get_body_file(environ)
    tell = file.tell()
    body = file.read()
    file.seek(tell)
    return body




# 
# 
# class MaxLengthWrapper(object):
#     """Wrapper around file-like objects to ensure that they recieve only as
#     much data as we have permitted them to.
# 
#     """
# 
#     def __init__(self, fh, max_length):
#         self.fh = fh
#         self.max_length = max_length
#         self.recieved = 0
#         self.seek = fh.seek
# 
#     def write(self, stuff):
#         self.recieved += len(stuff)
#         if self.max_length is not None and self.recieved > self.max_length:
#             raise ValueError("too much data recieved; got %d" % self.recieved)
#         return self.fh.write(stuff)
# 
# 
# def make_stringio(field):
#     """Simple make_file which returns a StringIO."""
#     return StringIO()
# 
# 
# def make_temp_file(field):
#     """Simple make_file which returns a temporary file.
# 
#     The underlaying file will be removed from the disk when this object is
#     garbage collected. See the tempfile module.
# 
#     """
#     # We do need the "+" in there for the tempfile module's sake.
#     import tempfile
#     return tempfile.TemporaryFile("w+b")
# 
# 
# class SingleField(cgi.FieldStorage):
# 
#     def __init__(self, parent, *args, **kwargs):
#         self.parent = weakref.proxy(parent)
#         self.made_file = False
#         cgi.FieldStorage.__init__(self, *args, **kwargs)
# 
#     @property
#     def key(self):
#         return self.name
# 
#     def make_file(self, binary=None):
#         self.made_file = True
#         max_file_length = self.parent.max_file_length
#         if max_file_length is not None and self.length > max_file_length:
#             raise ValueError("reported file size is too big: %r > %r" % (
#                 self.length, max_file_length))
#         return MaxLengthWrapper(self.parent.make_file(self), max_file_length)
#     
#     @property
#     def content_type(self):
#         return self.type
#     
#     @property
#     def content_type_options(self):
#         return self.type_options
#     
#     def __getattr__(self, name):
#         if name == 'value':
#             return cgi.FieldStorage.__getattr__(self, name)
#         return getattr(self.file, name)
# 
# 
# class FieldStorage(cgi.FieldStorage):
#     
#     def __init__(self, environ, make_file=None, max_file_length=None, keep_blank_values=True):
#         if make_file is not None:
#             self.make_file = make_file
#         self.max_file_length = max_file_length
#         environ = environ.copy()
#         environ['QUERY_STRING'] = ''
#         cgi.FieldStorage.__init__(self, 
#             fp=environ['wsgi.input'],
#             environ=environ,
#             keep_blank_values=keep_blank_values
#         )
#             
#     def FieldStorageClass(self, *args, **kwargs):
#         return SingleField(self, *args, **kwargs)
#     
#     def read_single(self):
#         # We don't take non urlencoded or multipart/form-data. But we must
#         # take special care to make sure something was actually sent before
#         # erroring, because jQuery (and others) change the Content-Type to
#         # text/plain if the ajax post has no content.
#         if self.length == 0:
#             return
#         if self.length > 0:
#             raise ValueError("we don't understand %r content-type" %
#                 self.type)
#         if self.fp.read(1):
#             raise ValueError("we don't understand %r content-type" %
#                 self.type)
#         return
#     
#     def make_file(self, field):
#         """Create the file object for the given field to write into.
#         
#         This is given a SingleField object (which extends cgi.FieldStorage)
#         and must return a file-like object to store the contents.
#         
#         Defaults to raising a ValueError to stop all posted files.
#         
#         """
#         raise ValueError("no make_file set; not accepting posted files")
# 
# 
# 
# 
# 
# def parse_body(environ, make_file=None, max_file_length=None, cache_body=True,
#         post_key=None, files_key=None, body_cache_key=None
#     ):
#     
#     post_key  = post_key or ENVIRON_POST_KEY
#     files_key = files_key or ENVIRON_FILES_KEY
#     
#     # Don't need to bother reparsing if we have already cached it.
#     if post_key in environ and files_key in environ:
#         return environ[post_key], environ[files_key]
#     
#     
#     post, files = MutableMultiMap(), MutableMultiMap()
#     environ[post_key] = post
#     environ[files_key] = files
#     
#     # Don't need to bother doing anything fancy if this is a GET
#     if environ['REQUEST_METHOD'].lower() in ('get', 'head'):
#         return post, files    
#     
#     # if cache_body:
#     #    assert_body_cache(environ, environ_key=body_cache_key)
#     
#     make_file = make_file or environ.get('nitrogen.body.make_file')
#     max_file_length = max_file_length or environ.get('nitrogen.max_file_length.make_file')
#     fs = FieldStorage(
#         environ=environ,
#         make_file=make_file,
#         max_file_length=max_file_length
#     )
#     
#     
#     # The list isn't always there. Try to post a empty string with
#     # jQuery and it sends content-type "text/plain", so fs.list will be None.
#     for chunk in fs.list or []:
#         charset = fs.type_options.get('charset', 'utf8')
#         if chunk.filename is not None:
#             # Using an attribute I added to FieldStorage to see if the internal
#             # StringIO is still in use.
#             if not chunk.made_file:
#                 contents = chunk.file.getvalue()
#                 chunk.file = chunk.make_file()
#                 chunk.file.write(contents)
#                 chunk.file.seek(0)
#             # Pull the actual files out of the MaxLengthWrapper(s).
#             if chunk.length >= 0 and chunk.file.recieved != chunk.length:
#                 raise ValueError("incorrect file length; got %d of %d" % (
#                     chunk.file.recieved, chunk.length))
#             chunk.length = chunk.file.recieved        
#             chunk.file = chunk.file.fh
#             files.append((chunk.name.decode(charset, 'error'), chunk))
#         else:
#             post.append((chunk.name.decode(charset, 'error'), chunk.value.decode(charset, 'error')))
#     
#     return post, files


CHARSET = 'utf-8'
ERRORS = 'replace'
ENVIRON_KEY = 'nitrogen.req.body'


def reject_factory(total_length, content_type, filename, file_length):
    """Do not accept files."""
    raise ValueError('not accepting files')


def stringio_factory(total_length, content_type, filename, file_length):
    return StringIO()


def temp_file_factory(total_length, content_type, filename, file_length):
    """Simple make_file which returns a temporary file.

    The underlaying file will be removed from the disk when this object is
    garbage collected. See the tempfile module.

    """
    # We do need the "+" in there for the tempfile module's sake.
    import tempfile
    return tempfile.TemporaryFile("w+b")


class StreamSizer(object):
    def __init__(self, stream):
        self.stream = stream
        self.size = 0
        self.seek = stream.seek
    def write(self, stuff):
        self.stream.write(stuff)
        self.size += len(stuff)

def wrap_stream_factory(factory):
    def new_factory(*args):
        return StreamSizer(factory(*args))
    return new_factory


def parse_body(environ, stream_factory=None, charset=None, errors=None,
    max_form_memory_size=None, max_content_length=None, silent=False, environ_key=ENVIRON_KEY):
    
    if environ_key not in environ:
        _, _, files = environ[environ_key] = wz.parse_form_data(environ,
            stream_factory=wrap_stream_factory(stream_factory or reject_factory),
            charset=charset or CHARSET,
            errors=errors or ERRORS,
            max_form_memory_size=max_form_memory_size,
            max_content_length=max_content_length,
            cls=MutableMultiMap,
            silent=silent
        )
        for file in files.itervalues():
            file.size = file.stream.size
            file.stream = file.stream.stream
        
    return environ[environ_key]
    
def parse_stream(*args, **kwargs):
    return parse_body(*args, **kwargs)[0]
                          
def parse_post(*args, **kwargs):
    return parse_body(*args, **kwargs)[1]
    
def parse_files(*args, **kwargs):
    return parse_body(*args, **kwargs)[2]



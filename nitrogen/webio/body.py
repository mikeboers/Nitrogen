
from cStringIO import StringIO
import cStringIO as cstringio
import functools
import io
import StringIO as stringio
import tempfile

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
    file = get_body_cache(environ)
    current_pos = file.tell()
    body = file.read()
    file.seek(current_pos)
    return body





CHARSET = 'utf-8'
ERRORS = 'replace'
ENVIRON_KEY = 'nitrogen.webio.body'


def reject_factory(total_length, content_type, filename, file_length):
    """Do not accept files."""
    raise ValueError('not accepting files')

def stringio_factory(total_length, content_type, filename, file_length):
    return StringIO()

def tempfile_factory(total_length, content_type, filename, file_length):
    """Simple make_file which returns a temporary file.

    The underlaying file will be removed from the disk when this object is
    garbage collected. See the tempfile module.

    """
    # We do need the "+" in there for the tempfile module's sake.
    return tempfile.TemporaryFile("w+b")

# For backwards compatibility.
temp_file_factory = tempfile_factory


class FileWrapper(object):
    
    def __init__(self, stream_factory, total_length, content_type, file_name, file_length):
        # We don't want empty file inputs to pull the file_name from the file
        # object itself. That leads to "<fdopen>" with the tempfile_factory.
        self.name = ''
        self.actual_length = 0
        # I feel this is the proper attribute name.
        self.file_name = file_name
        self.reported_length = file_length
        # I would rather call this "file", but I'm sticking with the werkzeug
        # naming scheme.
        self.stream = stream_factory(total_length, content_type, file_name, file_length)
    
    @classmethod
    def wrap(cls, factory):
        @functools.wraps(factory)
        def _wrapped_factory(*args):
            return cls(factory, *args)
        return _wrapped_factory
    
    def write(self, stuff):
        self.stream.write(stuff)
        self.actual_length += len(stuff)
    
    def __getattr__(self, name):
        return getattr(self.stream, name)
    
    def _done_recieving(self):
        del self.name


def parse_body(environ, stream_factory=None, charset=None, errors=None,
    max_form_memory_size=None, max_content_length=None, silent=False, environ_key=ENVIRON_KEY):
    
    if environ_key not in environ:
        _, _, files = environ[environ_key] = wz.parse_form_data(environ,
            stream_factory=FileWrapper.wrap(stream_factory or reject_factory),
            charset=charset or CHARSET,
            errors=errors or ERRORS,
            max_form_memory_size=max_form_memory_size,
            max_content_length=max_content_length,
            cls=MutableMultiMap,
            silent=silent
        )
        for file in files.itervalues():
            file._done_recieving()
    return environ[environ_key]
    
def parse_stream(*args, **kwargs):
    return parse_body(*args, **kwargs)[0]
                          
def parse_post(*args, **kwargs):
    return parse_body(*args, **kwargs)[1]
    
def parse_files(*args, **kwargs):
    return parse_body(*args, **kwargs)[2]



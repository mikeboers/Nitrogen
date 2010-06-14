
from cStringIO import StringIO
import cStringIO as cstringio
import StringIO as stringio
import io
import cgi

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



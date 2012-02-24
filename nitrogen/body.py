
from cStringIO import StringIO
import tempfile


def reject_factory(total_length, content_type, filename, file_length):
    """Do not accept files."""
    raise ValueError('not accepting posted files')

def stringio_factory(total_length, content_type, filename, file_length):
    return StringIO()

def tempfile_factory(total_length, content_type, filename, file_length):
    """Simple make_file which returns a temporary file.

    The underlaying file will be removed from the disk when this object is
    garbage collected. See the tempfile module.

    """
    # We do need the "+" in there for the tempfile module's sake.
    return tempfile.TemporaryFile("w+b")

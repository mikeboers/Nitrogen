"""Module for WSGI compression middleware.

I am well aware that this sort of thing is supposed to be left to the wsgi
server (http://www.python.org/dev/peps/pep-0333/#other-http-features) but in
practise my servers of choice (CGI, FastCGI, and a raw socket) do not have any
built in compression, and this has been working just fine for me.

In this module we have methods and classes for compression with gzip, zlib,
and deflate. Keep in mind that the "deflate" encoding specified by HTTP is
actually zlib, but IE doesn't seem to like that and is expecting raw deflate.

Therefore, we tend to send gzipped data, and then raw deflate (saying
"deflate" which means zlib... dumb).

I took the idea of stripping of the zlib headers from here:
http://stackoverflow.com/questions/1089662/python-inflate-and-deflate-implementations

"""

import zlib
import gzip
from wsgiref.headers import Headers
from cStringIO import StringIO
import logging


log = logging.getLogger(__name__)


def ZlibCompressor(level=9):
    """Class for incremental compression via zlib algo."""
    return zlib.compressobj(level)


def compress_zlib(data, level=9):
    """Compress some data via zlib algo."""
    return zlib.compress(data, level)


def decompress_zlib(data):
    """Decompress some zlibed data.

    Example:

        >>> data = "Hello, world!"
        >>> enc = compress_zlib(data)
        >>> enc != data
        True
        >>> dec = decompress_zlib(enc)
        >>> dec
        'Hello, world!'

    """
    return zlib.decompress(data)


class DeflateCompressor(object):
    """Class for incremental compression via deflate.

    Example:

        >>> obj = DeflateCompressor()
        >>> data = "Hello, world!"
        >>> enc = obj.compress(data)
        >>> enc += obj.flush()
        >>> enc != data
        True
        >>> dec = decompress_deflate(enc)
        >>> dec
        'Hello, world!'


    """
    def __init__(self, level=9):
        self.obj = zlib.compressobj(level)
        self.started = False

    def compress(self, data):
        if self.started:
            return self.obj.compress(data)
        self.started = True
        return self.obj.compress(data)[2:]

    def flush(self):
        return self.obj.flush()[:-4]


def compress_deflate(data, level=9):
    """Compress some data with deflate."""
    return zlib.compress(data, level)[2:-4]


def decompress_deflate(data):
    """Decompress some deflated data.

    Example:

        >>> data = "Hello, world!"
        >>> enc = compress_deflate(data)
        >>> enc != data
        True
        >>> dec = decompress_deflate(enc)
        >>> dec
        'Hello, world!'

    """
    # A negative window size surpresses headers.
    return zlib.decompress(data, -15)


class _GZipBuffer(list):
    """Helper class for GzipCompressor."""
    def __init__(self):
        self.write = self.append


class GzipCompressor(object):
    """Class to incrementally gzip a stream of data."""

    def __init__(self, level=9):
        self.buffer = _GZipBuffer()
        self.obj = gzip.GzipFile(mode='wb', compresslevel=level, fileobj=self.buffer)

    def _prep(self):
        ret = ''.join(self.buffer)
        self.buffer[:] = []
        return ret

    def compress(self, data):
        self.obj.write(data)
        return self._prep()

    def flush(self):
        self.obj.close()
        return self._prep()


def compress_gzip(data, level=9):
    """Compress some data with gzip."""
    obj = GzipCompressor(level)
    ret = obj.compress(data)
    ret += obj.flush()
    return ret


def decompress_gzip(data, level=9):
    """Decompress some gziped data.

    Example:

        >>> data = "Hello, world!"
        >>> enc = compress_gzip(data)
        >>> enc != data
        True
        >>> dec = decompress_gzip(enc)
        >>> dec
        'Hello, world!'

    """

    sio = StringIO(data)
    obj = gzip.GzipFile(mode='rb', fileobj=sio)
    return obj.read()


def compressor(app):
    log.warning(__name__ + '.compressor has been deprecated; use mod_deflate')
    return compressor



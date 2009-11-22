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
    def inner(environ, start):

        # Figure out which compression algos we are allowed to use
        algos = []
        algos_map = dict(
            gzip=GzipCompressor,
            deflate=DeflateCompressor
        )
        for algo in algos_map:
            if algo in environ.get('HTTP_ACCEPT_ENCODING', '').lower():
                algos.append(algo)

        def inner_start(status, headers, exc_info=None):
            headers = Headers(headers)
            if 'content-encoding' in headers:
                algos[:] = []
            if algos:
                headers['Content-Encoding'] = algos[0]
            start(status, headers.items())

        # Do the compression.
        compressor = None
        for x in app(environ, inner_start):
            if compressor is None:
                if algos:
                    compressor = algos_map[algos[0]]()
                else:
                    compressor = False
            x = compressor.compress(x) if compressor else x
            yield x
        if compressor:
            yield compressor.flush()

    return inner







def test_compress_plain():
    """Nose test, checking that plaintext is returned."""

    from webtest import TestApp

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield 'Hello, world!'
    app = TestApp(app)

    res = app.get('/')
    assert 'Content-Encoding' not in res.headers, "Content encoding is set."
    assert res.body == 'Hello, world!', "Output is wrong."


def test_compress_chunked():
    """Nose test, checking that plaintext is returned."""

    from webtest import TestApp

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text-plain'),
            ('Content-Encoding', 'chunked')])
        yield 'Hello, world!'
    app = TestApp(app)

    res = app.get('/')
    assert 'Content-Encoding' in res.headers, "Content encoding is not set."
    assert res.headers['Content-Encoding'] == 'chunked', "Content encoding has been changed."
    assert res.body == 'Hello, world!', "Output is wrong."


def test_compress_deflate():
    """Nose test, checking that compressed data is returned."""

    from webtest import TestApp

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "Hello, world!"
    app = compressor(app)
    app = TestApp(app)


    res = app.get('/', extra_environ={'HTTP_ACCEPT_ENCODING': 'other1,deflate,other2'})

    assert 'Content-Encoding' in res.headers, "Did not get content encoding."
    assert res.headers['Content-Encoding'] == 'deflate', "Wrong content encoding."

    assert res.body != 'Hello, world!', "Recieved plaintext."
    output = decompress_deflate(res.body)
    assert output == "Hello, world!", "Failed decode."



def test_compress_deflate():
    """Nose test, checking that compressed data is returned."""

    from webtest import TestApp

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "Hello, world!"
    app = compressor(app)
    app = TestApp(app)


    res = app.get('/', extra_environ={'HTTP_ACCEPT_ENCODING': 'other1,gzip,other2'})

    assert 'Content-Encoding' in res.headers, "Did not get content encoding."
    assert res.headers['Content-Encoding'] == 'gzip', "Wrong content encoding."

    assert res.body != 'Hello, world!', "Recieved plaintext."
    output = decompress_gzip(res.body)
    assert output == "Hello, world!", "Failed decode."


def test_compress_either():
    """Nose test, checking that compressed data is returned."""

    from webtest import TestApp

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "Hello, world!"
    app = compressor(app)
    app = TestApp(app)


    res = app.get('/', extra_environ={'HTTP_ACCEPT_ENCODING': 'gzip,deflate'})

    assert 'Content-Encoding' in res.headers, "Did not get content encoding."
    assert res.headers['Content-Encoding'] == 'gzip', "Wrong content encoding."

    assert res.body != 'Hello, world!', "Recieved plaintext."
    output = decompress_gzip(res.body)
    assert output == "Hello, world!", "Failed decode."



if __name__ == '__main__':
    from test import run
    run()

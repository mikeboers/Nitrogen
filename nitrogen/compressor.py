"""Module for WSGI compression middlewear.

I am well aware that this sort of thing is supposed to be left to the wsgi
server (http://www.python.org/dev/peps/pep-0333/#other-http-features) but in
practise my servers of choice (CGI, FastCGI, and a raw socket) do not have any
built in compression, and this has been working just fine for me.

I am also aware that I am handling this wrong. I am passing down a raw zlib
stream while telling the client that I am sending deflate (technically
"deflate" and "gzip" are both different wrappers around the raw zlip algo.
See: http://www.iana.org/assignments/http-parameters).

Oh well!

"""

import zlib

__all__ = ['compressor']

def compressor(app):
    def inner(environ, start):
        if 'deflate' not in environ.get('HTTP_ACCEPT_ENCODING', '').lower():
            for x in app(environ, start):
                yield x
            return
        def inner_start(status, headers):
            headers.append(('Content-Encoding', 'deflate'))
            start(status, headers)
        compressor = zlib.compressobj()
        for x in app(environ, inner_start):
            x = compressor.compress(x) if x else ''
            yield x
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
    output = zlib.decompress(res.body)
    assert output == "Hello, world!", "Failed decode."
    

if __name__ == '__main__':
    from test import run
    run()
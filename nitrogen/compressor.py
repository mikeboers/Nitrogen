import zlib

__all__ = ['middlewear']

def compressor(app):
    def inner(environ, start):
        if 'deflate' not in environ.get('HTTP_ACCEPT_ENCODING', '').split(','):
            for x in app(environ, start):
                yield x
            return
        def inner_start(status, headers):
            headers.append(('Content-Encoding', 'deflate'))
            start(status, headers)
        compressor = zlib.compressobj()
        for x in app(environ, inner_start):
            x = compressor.compress(x) if x else None
            if x:
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
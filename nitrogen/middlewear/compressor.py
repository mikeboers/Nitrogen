import zlib

__all__ = ['compressor']

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
    
    from nitrogen.test import WSGIServer
    
    def app(environ, start):
        start('200 OK', [])
        yield 'Hello, world!'
    
    status, headers, output = WSGIServer(compressor(app)).run()
    
    headers = dict(headers)
    assert 'Content-Encoding' not in headers, "Content encoding is set."
    
    assert output == 'Hello, world!', "Output is wrong."

def test_compress_deflate():
    """Nose test, checking that compressed data is returned."""
    
    from nitrogen.test import WSGIServer
    
    def app(environ, start):
        start('200 OK', [])
        yield "Hello, world!"
    
    server = WSGIServer(compressor(app))
    server.environ['HTTP_ACCEPT_ENCODING'] = 'other1,deflate,other2'
    status, headers, output = server.run()
    
    headers = dict(headers)
    assert 'Content-Encoding' in headers, "Did not get content encoding."
    assert headers['Content-Encoding'] == 'deflate', "Wrong content encoding."
    
    assert output != 'Hello, world!', "Recieved plaintext."
    output = zlib.decompress(output)
    assert output == "Hello, world!", "Failed decode."
    

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')
    from nitrogen.test import run
    run()
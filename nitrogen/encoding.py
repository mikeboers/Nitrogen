# content-encoding: utf-8

"""Module for UTF-8 encoding WSGI middleware.

It is currently not very tolerant about other encodings being used behind it's
back, but if I ever need them I will deal with them at that time.

"""

def utf8_encoder(app):
    """WSGI middleware that encodes everything to a UTF-8 string.
    
    Forces text/* content types to have a UTF-8 charset.
    If there is no Content-Type, it adds a utf8 plain text one.
    """
    def inner(environ, start):
        def inner_start(status, headers):
            has_type = False
            for i, h in enumerate(headers):
                if h[0].lower() == 'content-type':
                    has_type = True
                    if h[1].startswith('text/'):
                        if 'charset' not in h[1].lower():
                            headers[i] = (h[0], h[1].strip() + '; charset=UTF-8')
                        elif 'utf-8' not in h[1].lower() and 'utf8' not in h[1].lower():
                            raise ValueError('Content-Type header has non UTF-8 charset: %r.' % h[1])
            if not has_type:
                headers.append(('Content-Type', 'text/plain; charset=UTF-8'))
            start(status, headers)
        for x in app(environ, inner_start):
            if not isinstance(x, unicode):
                x = unicode(x, 'utf8', 'replace')
            # Should this be ascii? Then all the unicode characters go as XML refs.
            yield x.encode('utf8', 'xmlcharrefreplace')
    return inner


def test_utf8_encoder():
    """Nose test, checking that plaintext is returned."""

    from webtest import TestApp
    
    @utf8_encoder
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield u'¡™£¢∞§¶•ªº'
    app = TestApp(app)

    res = app.get('/')
    assert res.headers['content-type'] == 'text/plain; charset=UTF-8', 'Wrong content type.'
    assert res.body == u'¡™£¢∞§¶•ªº'.encode('utf8'), 'Not encoded properly.'

if __name__ == '__main__':
    from test import run
    run()
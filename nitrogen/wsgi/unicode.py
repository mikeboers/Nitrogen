# content-encoding: utf-8

"""Module for UTF-8 encoding WSGI middleware.

It is currently not very tolerant about other encodings being used behind it's
back, but if I ever need them I will deal with them at that time.

"""


import logging


log = logging.getLogger(__name__)


def utf8_encoder(app):
    """WSGI middleware that encodes everything to a UTF-8 string.
    
    Forces text/* content types to have a UTF-8 charset.
    If there is no Content-Type, it adds a utf8 plain text one.
    """
    def utf8_encoder_app(environ, start):
        if 'utf-8' not in environ.get('HTTP_ACCEPT_CHARSET', '').lower():
            for x in app(environ, start):
                if isinstance(x, unicode):
                    yield x.encode('ascii', 'xmlcharrefreplace')
                else:
                    yield str(x)
            return
        def utf8_encoder_start(status, headers, exc_info=None):
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
        for x in app(environ, utf8_encoder_start):
            if isinstance(x, unicode):
                x = x.encode('utf8', 'xmlcharrefreplace')
            elif not isinstance(x, str):
                x = str(x)
            yield x
    return utf8_encoder_app


def test_utf8_encoder():
    """Nose test, checking that plaintext is returned."""

    from webtest import TestApp
    
    @utf8_encoder
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield u'¡™£¢∞§¶•ªº'
    app = TestApp(app)

    res = app.get('/')
    assert res.body == '&#161;&#8482;&#163;&#162;&#8734;&#167;&#182;&#8226;&#170;&#186;'
    
    res = app.get('/', headers=[('accept-charset', 'utf-8')])
    assert res.headers['content-type'] == 'text/plain; charset=UTF-8', 'Wrong content type.'
    assert res.body == u'¡™£¢∞§¶•ªº'.encode('utf8'), 'Not encoded properly.'

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
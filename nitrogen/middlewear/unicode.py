import logging
def utf8_encoder(app):
    """Encodes everything to a UTF-8 string.
    Forces test/* content types to have a UTF-8 charset.
    If there is not Content-Type, it adds a utf8 plain text one.
    """
    def inner(environ, start):
        def app_start(status, headers):
            has_type = False
            for i, h in enumerate(headers):
                if h[0] == 'Content-Type':
                    has_type = True
                    if h[1].startswith('text'):
                        if 'charset' not in h[1]:
                            headers[i] = (h[0], h[1] + ';charset=UTF-8')
                        elif 'UTF-8' not in h[1]:
                            raise ValueError('Content-Type header has non UTF-8 charset: %r.' % h[1])
            if not has_type:
                headers.append(('Content-Type', 'text/plain;charset=UTF-8'))
            start(status, headers)
        for x in app(environ, app_start):
            if not isinstance(x, unicode):
                x = unicode(x, 'utf8', 'replace')
            # TODO: Should this be ascii? Then all the unicode characters go as XML refs.
            yield x.encode('utf8', 'xmlcharrefreplace')
    return inner
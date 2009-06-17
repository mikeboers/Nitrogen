import traceback
import logging

try:
    from .cookie import Container as CookieContainer
    from .input import Get, Post
    from .status import resolve_status
    from .error import format_error_report
except ValueError: # In case we are running local tests.
    from cookie import Container as CookieContainer
    from input import Get, Post
    from status import resolve_status
    from error import format_error_report

def utf8_encoder(app):
    """Encodes everything to a UTF-8 string.
    Forces test/* content types to have a UTF-8 charset.
    """
    def inner(environ, start):
        def app_start(status, headers):
            for i, h in enumerate(headers):
                if h[0] == 'Content-Type' and h[1].startswith('text'):
                    if 'charset' not in h[1]:
                        headers[i] = (h[0], h[1] + ';charset=UTF-8')
                    elif 'UTF-8' not in h[1]:
                        raise ValueError('Content-Type header has non UTF-8 charset: %r.' % h[1])
            start(status, headers)
        for x in app(environ, app_start):
            if not isinstance(x, unicode):
                x = unicode(x, 'utf8', 'replace')
            yield x.encode('utf8', 'xmlcharrefreplace')
    return inner

def cookie_parser(app):
    def inner(environ, start):
        environ['nitrogen.cookies'] = CookieContainer(environ.get('HTTP_COOKIE', ''))
        logging.warning('here')
        return app(environ, start)    
    return inner

def cookie_builder(app):
    def inner(environ, start):
        def inner_start(status, headers):
            cookies = environ.get('nitrogen.cookies')
            if cookies:
                environ['nitrogen.cookies']
                headers.extend(cookies.build_headers())
            start(status, headers)
        return app(environ, inner_start)
    return inner

def get_parser(app):
    def inner(environ, start):
        environ['nitrogen.get'] = Get(environ)
        return app(environ, start)
    return inner

def post_parser(app):
    def inner(environ, start):
        environ['nitrogen.post'] = Post(environ)
        return app(environ, start)
    return inner

def full_parser(app):
    return cookie_builder(post_parser(get_parser(cookie_parser(app))))



def status_resolver(app):
    def inner(environ, start):
        def inner_start(status, headers):
            start(resolve_status(status), headers)
        return app(environ, inner_start)
    return inner

def debugger(app):
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.output = []
            self.status = None
            self.headers = None
            
        def app_start(self, status, headers):
            self.status = status
            self.headers = headers
        
        def __iter__(self):
            try:
                for x in app(self.environ, self.app_start):
                    self.output.append(x)
                self.start(self.status, self.headers)
                for x in self.output:
                    yield x
            
            except Exception as e:
                report = format_error_report(self.environ, output=self.output)
                logging.error('nitrogen.wsgi.middlewear.debugger caught %r\n' % e + report)
                tb = traceback.format_exc()
                try:
                    self.start('500 Server Error', [
                        ('Content-Type', 'text/plain')
                    ])
                except:
                    pass
                yield report
    return inner


if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."

import traceback
import logging
import zlib
import threading

try:
    from .. import cookie
    from ..status import resolve_status
    from ..error import format_error_report
    from .compressor import compressor
    from .input import input_parser
    from .. import logs
except ValueError: # In case we are running local tests.
    import sys
    sys.path.insert(0, '..')
    import cookie
    from status import resolve_status
    from error import format_error_report
    from compressor import compressor
    import logs


class log_extra_filler(object):
    def __init__(self, app):
        self.app = app
        self.thread_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        if not hasattr(logs.extra, 'thread_i'):
            self.lock.acquire()
            self.thread_count += 1
            logs.extra.thread_i = self.thread_count
            self.lock.release()
        logs.extra.ip = environ.get('REMOTE_ADDR')
        return self.app(environ, start)
                        
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

def cookie_parser(app, hmac_key=None):
    class_ = cookie.make_signed_container(hmac_key) if hmac_key else cookie.Container
    def inner(environ, start):
        environ['nitrogen.cookies'] = class_(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return inner

def cookie_builder(app, strict=True):
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.headers = None
    
        def inner_start(self, status, headers):
            cookies = self.environ.get('nitrogen.cookies')
            if cookies:
                self.headers = cookies.build_headers()
                headers.extend(self.headers)
            self.start(status, headers)
        
        def __iter__(self):    
            for x in app(self.environ, self.inner_start):
                yield x
            if not strict:
                return
            cookies = self.environ.get('nitrogen.cookies')
            if cookies is None:
                raise ValueError('Cookies have been removed from environ.')
            headers = cookies.build_headers()
            if self.headers is not None and self.headers != headers:
                raise ValueError('Cookies have been modified since WSGI start.', self.headers, headers)
    return inner

def full_parser(app, hmac_key=None, strict=True):
    return cookie_builder(
        input_parser(cookie_parser(app, hmac_key=hmac_key)),
        strict=strict
    )



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
    from test import run
    run()

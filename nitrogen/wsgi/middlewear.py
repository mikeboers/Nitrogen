import httplib
import traceback
from .cookie import Container as CookieContainer
from .input import Get, Post

def cookie_parser(app):
    def inner(environ, start):
        environ['nitrogen.cookies'] = CookieContainer(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
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
    return post_parser(get_parser(cookie_parser(app)))

def status_helper(app):
    def inner(environ, start):
        def inner_start(status, headers):

            if status is None:
                start('200 OK', headers)
                return

            # First see if the constant is set
            status_no = getattr(httplib, str(status).replace(' ', '_').upper(), None)
            if status_no is not None:
                start('%d %s' % (status_no, httplib.responses[status_no]), headers)
                return

            # See if status is a status code.
            if status in httplib.responses:
                start('%d %s' % (status, httplib.responses[status]), headers)
                return

            # Just try what we were given.
            start(status, headers)

        return app(environ, inner_start)

    return inner

def debugger(app):
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.output = []
        
        def app_start(self, status, headers):
            self.status = status
            self.headers = headers
        
        def __iter__(self):
            try:
                for x in app(self.environ, self.app_start):
                    self.output.append(str(x))
                self.start(self.status, self.headers)
                for x in self.output:
                    yield x
            
            except Exception as e:
                tb = traceback.format_exc()
                self.start('500 Server Error', [
                    ('Content-Type', 'text/plain')
                ])
                yield 'UNCAUGHT EXCEPTION\n'
                yield tb
                yield '\n'
                yield 'Buffered %d chunks.\n' % len(self.output)
                yield '=' * 80 + '\n'
                for x in self.output:
                    yield x
    return inner




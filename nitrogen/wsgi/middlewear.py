import traceback

try:
    from .cookie import Container as CookieContainer
    from .input import Get, Post
    from .status import resolve_status
except ValueError: # In case we are running local tests.
    from cookie import Container as CookieContainer
    from input import Get, Post
    from status import resolve_status

def cookie_parser(app):
    def inner(environ, start):
        environ['nitrogen.cookies'] = CookieContainer(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return inner

def cookie_builder(app):
    def inner(environ, start):
        def inner_start(status, headers):
            cookies = environ.get('nitrogen.cookies')
            if cookies:
                del environ['nitrogen.cookies']
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
                    self.output.append(str(x))
                self.start(self.status, self.headers)
                for x in self.output:
                    yield x
            
            except Exception as e:
                tb = traceback.format_exc()
                try:
                    self.start('500 Server Error', [
                        ('Content-Type', 'text/plain')
                    ])
                except:
                    pass
                yield 'UNCAUGHT EXCEPTION\n'
                yield tb
                yield '\n'
                yield 'Buffered %d chunks.\n' % len(self.output)
                yield '=' * 80 + '\n'
                for x in self.output:
                    yield x
    return inner


if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."

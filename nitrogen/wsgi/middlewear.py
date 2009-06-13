import httplib
import traceback

try:
    from .cookie import Container as CookieContainer
    from .input import Get, Post
except ValueError: # In case we are running local tests.
    from cookie import Container as CookieContainer
    from input import Get, Post

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

def _resolve_status(status):
    """Resolve a given object into the status that it should represent.
    
    Examples:
        >>> _resolve_status(200)
        '200 OK'
        >>> _resolve_status(404)
        '404 Not Found'
        >>> _resolve_status('UNAUTHORIZED')
        '401 Unauthorized'
        >>> _resolve_status(None)
        '200 OK'
        >>> _resolve_status('314159 Not in list')
        '314159 Not in list'
    """
    
    # None implies 200.
    if status is None:
        return '200 OK'
    # See if status is a status code.
    if status in httplib.responses:
        return '%d %s' % (status, httplib.responses[status])
    # See if the constant is set
    status_no = getattr(httplib, str(status).replace(' ', '_').upper(), None)
    if status_no is not None:
        return '%d %s' % (status_no, httplib.responses[status_no])
    # Can't find it... just hand it back.
    return status

def status_resolver(app):
    def inner(environ, start):
        def inner_start(status, headers):
            start(_resolve_status(status), headers)
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


if __name__ == '__main__':
    import doctest
    print "Testing..."
    doctest.testmod()
    print "Done."

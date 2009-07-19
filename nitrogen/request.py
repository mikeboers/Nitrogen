"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""

from __future__ import print_function

from StringIO import StringIO

from status import resolve_status

from middlewear.input import input_parser
from cookie import Container as CookieContainer

class HeaderList(list):
    '''A more dict-like list for headers.'''
    
    def __setitem__(self, key, value):
        '''Appends a header with item access.
        
        Does not check to see if the header is already set. Multiple headers
        with the same key can be created this way.
        
        '''
        if isinstance(key, basestring):
            self.append((key, value))
        else:
            list.__setitem__(self, key, value)

class Request(object):
    
    def __init__(self, environ, start):
        self.environ = environ
        self._start = start
        
        self._has_started = False
        self._buffer = StringIO()
        
        if environ.get('nitrogen.get') is None:
            input_parser(environ=environ)
            
        self.get = environ['nitrogen.get']    
        self.post = environ['nitrogen.post']
        self.files = environ['nitrogen.files']
        
        self.cookies = environ.get('nitrogen.cookies')    
        self._cookies_provided = self.cookies is not None
        if self.cookies is None:
            self.cookies = CookieContainer(environ.get('HTTP_COOKIE', ''))
        
        # self.unrouted = environ.get('nitrogen.path.unrouted')
        # self.routed = environ.get('nitrogen.path.routed')
        
        self.status = '200 OK'
        self.headers = HeaderList()
    
    def start(self, status=None, headers=None, html=None):
        """Start the wsgi return sequence.
        
        If called with status, that status is resolved. If status is None, we
        use the internal status.
        
        If headers are supplied, they are sent after those that have been
        added to self.headers.
        """
        
        if self._has_started:
            raise ValueError("wsgi start has already been called.")
        self._has_started = True
        
        headers = self.headers + (list(headers) if headers else [])
        if not self._cookies_provided:
            headers.extend(self.cookies.build_headers())
        
        if html:
            headers.append(('Content-Type', 'text/html'))
        
        self._start(resolve_status(status or self.status), headers)
    
    def write(self, *args, **kwargs):
        self._buffer.write(*args, **kwargs)
    
    def print(self, *args, **kwargs):
        kwargs['file'] = kwargs.get('file', self._buffer)
        print(*args, **kwargs)
    
    def __str__(self):
        return self._buffer.getvalue()
    
    def __iter__(self):
        if not self._has_started:
            self.start()
        yield self._buffer.getvalue()
    
    @property
    def is_get(self):
        return self.environ.get('REQUEST_METHOD') == 'GET'
        
    @property
    def is_post(self):
        return self.environ.get('REQUEST_METHOD') == 'POST'
    
    @property
    def method(self):
        return self.environ.get('REQUEST_METHOD')
    
    @property
    def user(self):
        return self.environ.get('app.user')
    
    @property
    def is_admin_area(self):
        return self.environ.get('SERVER_NAME', '').startswith('admin.')

# This has a bad name... Shame on me.
# TODO: Name this better.
def request_handler(app):
    """Decorator for converting WSGI based apps into request handling apps."""
    def inner(environ, start, *args):
        req = Request(environ, start)
        return app(req, *args)
    return inner

def request_handler_method(app):
    """Decorator for converting WSGI based instance methods into request handling apps."""
    def inner(self, environ, start, *args):
        req = Request(environ, start)
        return app(self, req, *args)
    return inner
    
if __name__ == '__main__':
    from test import run
    run()



"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

from StringIO import StringIO

from status import resolve_status

from webio import request_params
from cookie import Container as CookieContainer
from headers import DelayedHeaders, MutableHeaders

class _Common(object):
    pass

def _environ_getter(key, callback=None):
    if callback:
        def getter(self):
            return callback(self.environ.get(key))
    else:
        def getter(self):
            return self.environ.get(key)
    return property(getter)

def _attr_getter(key):
    def getter(self):
        return getattr(self, key)
    return property(getter)

class Request(_Common):
    
    def __init__(self, environ, start=None):
        self._environ = environ
        if start:
            self._response = Response(start)
    
    environ = _attr_getter('_environ')
    response = _attr_getter('_response')
    
    is_get = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'GET')
    is_post = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'POST')
    is_put = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'PUT')
    is_delete = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'DELETE')
    is_head = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'HEAD')
    
    get = _environ_getter('nitrogen.get')
    post = _environ_getter('nitrogen.post')
    files = _environ_getter('nitrogen.files')
    cookies = _environ_getter('nitrogen.cookies')
    headers = _environ_getter('nitrogen.headers')
    
    method = _environ_getter('REQUEST_METHOD', str.upper)
    user = _environ_getter('app.user')
    
    @property
    def is_admin_area(self):
        return self.environ.get('SERVER_NAME', '').startswith('admin.')

def _content_type_property(spec):
    @property
    def prop(self):
        return self.content_type == spec
    @prop.setter
    def prop(self, value):
        if not value:
            raise ValueError('cannot be set to non-true value')
        self.content_type = spec
    return prop
        
class Response(_Common):
    
    def __init__(self, start):
        self._start = start
        self._headers = MutableHeaders()
        
        self._status = None
        self.status = '200 OK'
        
        self.content_type = 'text/html'
        self.charset = 'utf-8'
    
    headers = _attr_getter('_headers')
    
    as_html = _content_type_property('text/html')
    as_text = _content_type_property('text/plain')
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        self._status = resolve_status(value)
    
    def start(self, status=None, headers=None, plain=None, html=None):
        """Start the wsgi return sequence.

        If called with status, that status is resolved. If status is None, we
        use the internal status.

        If headers are supplied, they are sent after those that have been
        added to self.headers.
        """
        
        status = resolve_status(status) if status is not None else self.status
        
        # Deal with content-type overrides and properties.
        if plain or html:
            del self.headers['content-type']
            if html:
                self.content_type = 'text/html'
            else:
                self.content_type = 'text/plain'
        if plain or html or 'content-type' not in self.headers:
            if self.charset:
                self.headers['content-type'] = '%s; charset=%s' % (
                    self.content_type, self.charset)
            else:
                self.headers['content-type'] = self.content_type
        
        headers = self.headers.allitems() + (list(headers) if headers else [])
        
        self._start(status, headers)



def test_request_get():
    def app(environ, start):
        req = Request(environ, start)
        assert req.method == 'GET'
        assert req.is_get
        assert not req.is_post
        assert req.get['key'] == 'value'
        
        res = req.response
        res.as_text = True
        print res.content_type
        res.start()
        
        yield 'Hello, World!'
    
    app = TestApp(request_params(app))
    res = app.get('/?key=value')
    assert res.headers['content-type'] == 'text/plain; charset=utf-8'
    
if __name__ == '__main__':
    from . import test
    from webtest import TestApp
    from webio import request_params
    test.run()
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

from webtest import TestApp

from .status import resolve_status
from .webio import request_params
from .cookie import Container as CookieContainer
from .headers import DelayedHeaders, MutableHeaders
from .webio import request_params
from .route.tools import get_data

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
        
        self.route = get_data(environ)
    
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
    
    etag = _environ_getter('HTTP_IF_NONE_MATCH')
    
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

def _header_setter(key, get=None, set=None):
    if get is None:
        @property
        def prop(self):
            return self.headers.get(key)
    else:
        @property
        def prop(self):
            return get(self.headers.get(key))
    if set is None:
        @prop.setter
        def prop(self, value):
            self.headers[key] = value
    else:
        @prop.setter
        def prop(self, value):
            self.headers[key] = set(value)
    return prop

class Response(_Common):
    
    def __init__(self, start):
        self._start = start
        self._headers = MutableHeaders()
        
        self._status = None
        self.status = '200 OK'
        
        self._content_type = 'text/html'
        self._charset = 'utf-8'
        self._build_content_type_header()
        
        self._filename = None
    
    headers = _attr_getter('_headers')
    
    as_html = _content_type_property('text/html')
    as_text = _content_type_property('text/plain')
    
    etag = _header_setter('etag')
    location = _header_setter('location')
    
    @property
    def filename(self):
        return self._filename
    
    @filename.setter
    def filename(self, value):
        self._filename = None if value is None else str(value)
        if self._filename is not None:
            self.headers.content_disposition = 'attachment; filename="%s"' % self.filename.replace('"', '\\"')
        else:
            del self.headers['content-disposition']
        
    @property
    def content_type(self):
        return self._content_type
    
    @content_type.setter
    def content_type(self, value):
        self._content_type = value
        self._build_content_type_header()
    
    @property
    def charset(self):
        return self._charset
    
    @charset.setter
    def charset(self, value):
        self._charset = value
        self._build_content_type_header()
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        self._status = resolve_status(value)
    
    def _build_content_type_header(self):
        if self.charset:
            self.headers['content-type'] = '%s; charset=%s' % (
                self.content_type, self.charset)
        else:
            self.headers['content-type'] = self.content_type
    
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
        
        # Deal with etag.
        if self.etag is not None:
            self.headers['etag'] = str(self.etag)
        
        headers = self.headers.allitems() + (list(headers) if headers else [])
        
        self._start(status, headers)


def as_request(app):
    """WSGI middleware to adapt WSGI style requests to a single Request object."""
    
    def inner(self, environ, start=None):
        if start is None:
            self, environ, start = start, self, environ
        request = Request(environ, start)
        if self:
            return app(self, request)
        return app(request)
    return inner


def test_request_get():
    def app(environ, start):
        req = Request(environ, start)
        assert req.method == 'GET'
        assert req.is_get
        assert not req.is_post
        assert req.get['key'] == 'value'

        res = req.response
        assert res.headers.content_type == 'text/html; charset=utf-8'
        res.as_text = True
        assert res.headers.content_type == 'text/plain; charset=utf-8'
        res.start()

        yield 'Hello, World!'

    app = TestApp(request_params(app))
    res = app.get('/?key=value')
    assert res.headers['content-type'] == 'text/plain; charset=utf-8'

def test_request_get_file():
    def app(environ, start):
        req = Request(environ, start)
        res = req.response
        res.filename = 'hello.txt'
        assert res.headers.content_disposition == 'attachment; filename="hello.txt"'
        res.filename = 'hello"world.quoted'
        assert res.headers.content_disposition == 'attachment; filename="hello\\"world.quoted"'
        
        res.start()

        yield 'Hello, World!'

    app = TestApp(request_params(app))
    res = app.get('/')

def test_request_post_and_etag():
    def app(environ, start):
        req = Request(environ, start)
        assert req.method == 'POST'
        assert req.is_post
        assert not req.is_get
        assert len(req.get) == 0
        assert req.post['key'] == 'value'
        assert req.etag == 'etag_goes_here'

        res = req.response
        res.as_html = True
        assert res.headers.content_type == 'text/html; charset=utf-8'
        res.etag = 'new_etag'
        res.start()

        yield 'Hello, World!'

    app = TestApp(request_params(app))
    res = app.post('/', {'key': 'value'}, headers=[('if_none_match', 'etag_goes_here')])
    assert res.headers['content-type'] == 'text/html; charset=utf-8'
    assert res.headers['etag'] == 'new_etag'
    
if __name__ == '__main__':
    from . import test
    test.run()
"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""


from cStringIO import StringIO
import re
import logging
from cgi import parse_header
import base64

from webtest import TestApp

from .http.status import resolve_status
from .http.time import parse_http_time, format_http_time
from .webio import request_params
from .cookie import Container as CookieContainer
from .headers import DelayedHeaders, MutableHeaders
from .webio import request_params
from .route.tools import get_data as get_route_data, get_unrouted


log = logging.getLogger(__name__)

def _environ_getter(key, callback=None):
    """Builds a property for getting values out of the environ.
    
    A callback can be specified to modify the return value.
    
    """
    
    if callback:
        def getter(self):
            return callback(self.environ.get(key))
    else:
        def getter(self):
            return self.environ.get(key)
    return property(getter)


def _environ_time_getter(key):
    """Builds a property for getting times out of the environ.
    
    An unparsable time results in None.
    
    TODO: test for what bad dates do
    """
    
    def getter(self):
        v = self.environ.get(key)
        if v is None:
            return None
        try:
            dt = parse_http_time(v)
            return dt
        except ValueError:
            return None
    return property(getter)


def _attr_getter(key):
    """Builds a property which gets an attribute off the object."""
    def getter(self):
        return getattr(self, key)
    return property(getter)


class Request(object):
    
    """HTTP request abstraction class."""
    
    def __init__(self, environ):
        self.environ = environ
        
    @property
    def route(self):
        return get_route_data(self.environ)
    
    method = _environ_getter('REQUEST_METHOD', str.upper)
    is_get = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'GET')
    is_post = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'POST')
    is_put = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'PUT')
    is_delete = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'DELETE')
    is_head = _environ_getter('REQUEST_METHOD', lambda x: x.upper() == 'HEAD')
    
    # The objects these pull are provided by webio.request_params.
    get = _environ_getter('nitrogen.get')
    post = _environ_getter('nitrogen.post')
    files = _environ_getter('nitrogen.files')
    cookies = _environ_getter('nitrogen.cookies')
    headers = _environ_getter('nitrogen.headers')
    
    session = _environ_getter('beaker.session')
    
    # These two are the same. I just like `etag` much more.
    if_none_match = _environ_getter('HTTP_IF_NONE_MATCH')
    etag = _environ_getter('HTTP_IF_NONE_MATCH')
    
    # Other generic stuff.
    date = _environ_time_getter('HTTP_DATE')
    host = _environ_getter('HTTP_HOST')
    if_modified_since = _environ_time_getter('HTTP_IF_MODIFIED_SINCE')
    referer = _environ_getter('HTTP_REFERER')
    user_agent = _environ_getter('HTTP_USER_AGENT')
    
    @property
    def unrouted(self):
        return get_unrouted(self.environ)
    
    # @property
    # def basic_username(self):
    #     auth = self.headers.get('Authorization')
    #     if not auth:
    #         return None
    #     if not auth.startswith('Basic '):
    #         return None
    #     
    #     username, password = base64.b64decode(auth.split()[1]).split(':')
    #     return username
    
    
    # This will be handled another way soon.
    user = _environ_getter('app.user')
    
    @property
    def is_admin_area(self):
        return self.environ.get('SERVER_NAME', '').startswith('admin.')


def _content_type_property(spec):
    """Build a property for quick setting of content types.
    
    You can only set these properties to be True. When you do so, the content-
    type of the response is set to the type specified by `spec`.
    
    """
    
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
    """Build a header property.
    
    Optional get and set transform the header value on it's way in and out.
    
    """
    
    @property
    def prop(self):
        v = self.headers.get(key)
        return get(v) if get else v
        
    @prop.setter
    def prop(self, value):
        value = set(value) if set else value
        if value is None:
            self.headers.remove(key)
        else:
            self.headers[key] = value
    return prop


def _header_time_setter(key):
    """Build a header property which sets a time value.
    
    This property reveals a datetime interface, while it sets the actual
    header to a string.
    
    """
    
    @property
    def prop(self):
        x = self.headers.get(key)
        try:
            dt = parse_http_time(x)
            return dt
        except ValueError:
            pass
        return None
    
    @prop.setter
    def prop(self, value):
        if value is None:
            self.headers.remove(key)
        else:
            self.headers[key] = format_http_time(value)
            
    return prop


class Response(object):
    
    """HTTP response abstraction."""
    
    def __init__(self, start=None, headers=None):
        self._start = start
        self._headers = MutableHeaders(headers or [])
        
        self._status = None
        self.status = '200 OK'
        
        if 'content-type' in self.headers:
            ctype, cdict = parse_header(self.headers['content-type'])
            self._content_type = ctype
            self._charset = cdict.get('charset')
        else:
            self._content_type = 'text/html'
            self._charset = 'utf-8'
            self._build_content_type_header()
        
        self._filename = None
    
    headers = _attr_getter('_headers')
    
    as_html = _content_type_property('text/html')
    as_text = _content_type_property('text/plain')
    as_json = _content_type_property('application/json')
    
    etag = _header_setter('etag')
    location = _header_setter('location')
    
    date = _header_time_setter('date')
    last_modified = _header_time_setter('last-modified')
    expires = _header_time_setter('expires')
    
    @property
    def max_age(self):
        if 'cache-control' not in self.headers:
            return None
        m = re.search(r'max-age=(\d+)', self.headers['cache-control'])
        if not m:
            return None
        return int(m.group(1))
    
    @max_age.setter
    def max_age(self, value):
        # TODO: make this not overwrite other stuff.
        self.headers['cache-control'] = 'max-age=%d, must-revalidate' % value
    
    @property
    def filename(self):
        return self._filename
    
    @filename.setter
    def filename(self, value):
        self._filename = None if value is None else str(value)
        if self._filename is not None:
            self.headers.content_disposition = 'attachment; filename="%s"' % self.filename.replace('"', '\\"')
        else:
            self.headers.remove('content-disposition')
        
    @property
    def content_type(self):
        return self._content_type
    
    @content_type.setter
    def content_type(self, value):
        self._content_type = value
        self._build_content_type_header()
    
    type = content_type
    
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
        if self.content_type is None:
            self.headers.remove('content-type')
        elif self.charset:
            self.headers['content-type'] = '%s; charset=%s' % (
                self.content_type, self.charset)
        else:
            self.headers['content-type'] = self.content_type
    
    # @property
    # def basic_realm(self):
    #     auth = self.headers.get('WWW-Authenticate')
    #     if auth is None:
    #         return None
    #     mode, blob = auth.split()
    #     if mode.lower() != 'basic':
    #         return none
    #     if blob.startswith('realm="') and blob[-1] == '"':
    #         return blob[7:-1]
    #     return None
    # 
    # @basic_realm.setter
    # def basic_realm(self, value):
    #     self.headers['WWW-Authenticate'] = 'Basic realm="%s"' % value    
    
    def start(self, status=None, headers=None, plain=None, html=None, **kwargs):
        """Start the wsgi return sequence.

        If called with status, that status is resolved. If status is None, we
        use the internal status.

        If headers are supplied, they are sent after those that have been
        added to self.headers.
        """
        
        if not self._start:
            raise ValueError('no WSGI start')
        
        if status:
            self.status = status
        
        # Deal with content-type overrides and properties.
        if plain or html:
            log.warning('use of html/plain kwargs is depreciated')
            if html:
                self.content_type = 'text/html'
            else:
                self.content_type = 'text/plain'
        
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError('no request attribute %r' % k)
            setattr(self, k, v)
                
        headers = self.headers.allitems() + (list(headers) if headers else [])
        
        self._start(self.status, headers)


def as_request(app):
    """WSGI middleware to adapt WSGI style requests to a single Request object."""
    
    def inner(self, environ, start=None):
        if start is None:
            self, environ, start = start, self, environ
        request = Request(environ)
        response = Response(start)
        if self:
            return app(self, request, response)
        return app(request, response)
    return inner







def test_request_get():
    def app(environ, start):
        req = Request(environ)
        assert req.method == 'GET'
        assert req.is_get
        assert not req.is_post
        assert req.get['key'] == 'value'

        res = Response(start)
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
        req = Request(environ)
        res = Response(start)
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
        req = Request(environ)
        assert req.method == 'POST'
        assert req.is_post
        assert not req.is_get
        assert len(req.get) == 0
        assert req.post['key'] == 'value'
        assert req.etag == 'etag_goes_here'

        res = Response(start)
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

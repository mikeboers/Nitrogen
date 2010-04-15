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
import werkzeug as wz
import werkzeug.utils as wzutil

from multimap import MultiMap

from .http.status import resolve_status
from .http.time import parse_http_time, format_http_time
from .webio import request_params
from .webio.query import parse_query
from .webio.headers import parse_headers, MutableHeaders, EnvironHeaders
from .webio import cookies
from .webio.body import parse_post, parse_files
from .route.core import get_route_history, get_route_data


log = logging.getLogger(__name__)


def _environ_parser(func, *args, **kwargs):
    def parser(self):
        return func(self.environ, *args, **kwargs)
    return property(parser)



class Request(object):
    
    """WSGI/HTTP request abstraction class."""
    
    # The total maximum length of a POST (or PUT) request, including form data
    # and all files. See http://werkzeug.pocoo.org/documentation/0.6/http.html#werkzeug.parse_form_data
    # for more info.
    max_content_length = 2 * 1024 * 1028
    
    # Maximum size for all form data to accept. See http://werkzeug.pocoo.org/documentation/0.6/http.html#werkzeug.parse_form_data
    # for more info.
    max_form_memory_size = None
    
    # Function to use to create file objects at parse time. Defaults to
    # rejecting all files. See http://werkzeug.pocoo.org/documentation/0.6/http.html#werkzeug.parse_form_data
    # for more info.
    stream_factory = None
    
    response_class = None
    
    def __init__(self, environ, start=None, charset=None, decode_errors=None):
        self.environ = environ
        self.wsgi_start = start
        self.charset = charset
        self.decode_errors = decode_errors
    
    method = wz.environ_property('REQUEST_METHOD', load_func=str.upper)
    is_get = wz.environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'GET')
    is_post = wz.environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'POST')
    is_put = wz.environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'PUT')
    is_delete = wz.environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'DELETE')
    is_head = wz.environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'HEAD')
    
    @wz.cached_property
    def headers(self):
        return EnvironHeaders(self.environ)

    @wz.cached_property
    def response(self):
        return (self.response_class or Response)(request=self) if self.wsgi_start else None
    
    query_string = wz.environ_property('QUERY_STRING')
    @property
    def query(self):
        return parse_query(self.environ, charset=self.charset, errors=self.decode_errors)
    get = query # Depreciated
    
    @wz.cached_property
    def cookies(self):
        raw = cookies.parse_cookies(self.environ, charset=self.charset, decode_errors=self.decode_errors)
        # This is immutable, because it does not reflect back to the environ at this time.
        return MultiMap((k, c.value) for k, c in raw.iterallitems())
    
    @property
    def stream(self):
        return parse_stream(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
        
    @property
    def post(self):
        return parse_post(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
        
    @property
    def files(self):
        return parse_files(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
    
    session = wz.environ_property('beaker.session')
    
    @property
    def route_history(self):
        return get_route_history(self.environ)
    
    @property
    def url_for(self):
        return self.route_history.url_for
    
    @property
    def unrouted(self):
        return self.route_history[-1].path
    
    route = wz.environ_property('wsgiorg.routing_args', load_func=lambda x: x[1])    
    
    # This one gets a little more attension because IE 6 will send us the
    # length of the previous request as an option to this header
    if_modified_since = wz.environ_property('HTTP_IF_MODIFIED_SINCE', load_func=lambda x: wz.parse_date(wz.parse_options_header(x)[0]))
    if_unmodified_since = wz.environ_property('HTTP_IF_UNMODIFIED_SINCE', load_func=lambda x: wz.parse_date(wz.parse_options_header(x)[0]))
    
    # Lots of pretty generic headers...
    accept = wz.environ_property('HTTP_ACCEPT', load_func=lambda x: wz.parse_accept_header(x, wz.MIMEAccept))
    accept_charset = wz.environ_property('HTTP_ACCEPT_CHARSET', load_func=lambda x: wz.parse_accept_header(x, wz.CharsetAccept))
    accept_encoding = wz.environ_property('HTTP_ACCEPT_ENCODING', load_func=lambda x: wz.parse_accept_header(x, wz.Accept))
    accept_language = wz.environ_property('HTTP_ACCEPT_LANGUAGE', load_func=lambda x: wz.parse_accept_header(x, wz.LanguageAccept))
    authorization = wz.environ_property('HTTP_AUTHORIZATION', load_func=wz.parse_authorization_header)
    cache_control = wz.environ_property('HTTP_CACHE_CONTROL', load_func=wz.parse_cache_control_header)
    date = wz.environ_property('HTTP_DATE', load_func=wz.parse_date)
    etag = wz.environ_property('HTTP_IF_NONE_MATCH') # Same as if_none_match, but I have used this name before. Still depreciated.
    host = wz.environ_property('HTTP_HOST')
    if_match = wz.environ_property('HTTP_IF_MATCH')
    if_none_match = wz.environ_property('HTTP_IF_NONE_MATCH')
    path_info = wz.environ_property('PATH_INFO')
    referer = wz.environ_property('HTTP_REFERER')
    remote_addr = wz.environ_property('REMOTE_ADDR')
    remote_port = wz.environ_property('REMOTE_PORT', load_func=int)
    remote_user = wz.environ_property('REMOTE_USER')
    script_name = wz.environ_property('SCRIPT_NAME')
    user_agent = wz.environ_property('HTTP_USER_AGENT', load_func=wz.UserAgent)
    
    # WSGI stuff
    is_secure = wz.environ_property('wsgi.url_scheme', load_func=lambda x: x == 'https')
    is_multiprocess = wz.environ_property('wsgi.multiprocess')
    is_multithread = wz.environ_property('wsgi.multithread')
    is_run_once = wz.environ_property('wsgi.run_once')

    # Not sent by every library, but atleast jQuery, prototype and Mochikit
    # and probably some more.
    is_xhr = wz.environ_property('HTTP_X_REQUESTED_WITH', load_func=lambda x: (x or '').lower() == 'xmlhttprequest')
    is_ajax = is_xhr





def _content_type_flag(spec):
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


def _autoupdate_header(name, load_func):
    def on_update(obj):
        headers = obj._nitrogen_response.headers
        value = str(obj)
        if obj:
            headers[name] = obj
        else:
            try:
                del headers[name]
            except KeyError:
                pass
    def header_get(self):
        x = load_func(self.headers.get(name), on_update=on_update)
        x._nitrogen_response = self
        return x
    header_get.__name__ = name
    def header_set(self, v):
        if v is None:
            self.headers.discard(name)
        else:
            self.headers[name] = str(v)
    return property(header_get, header_set)


class Response(object):
    
    """HTTP response abstraction.
    
    Need to pass the request this is connected to if you want to use the maybe
    pre-build response cookies container."""
    
    def __init__(self, start=None, headers=None, request=None):
        self.wsgi_start = start
        self.headers = headers or []
        self.request = request
        
        self._status = '200 OK'
        self._charset = 'utf-8'
    
        if 'Content-Type' in self.headers:
            ctype, opts = wz.parse_options_header(self.headers['Content-Type'])
            self._charset = opts.get('charset')
                
        # Base the response cookie class off of the request cookies.
        if request:
            if start and request.wsgi_start:
                raise ValueError('given start and request with wsgi_start')
            self.wsgi_start = request.wsgi_start
    
    @wz.cached_property
    def cookies(self):
        return self.cookie_factory()
    
    @wz.cached_property
    def cookie_factory(self):
        if self.request is not None:
            return cookies.get_factory(self.request.environ)
        return cookies.Container
    
    @property
    def headers(self):
        return self._headers
    
    @headers.setter
    def headers(self, value):
        self._headers = value if isinstance(value, MutableHeaders) else MutableHeaders(value)
    
    as_html = _content_type_flag('text/html')
    as_text = _content_type_flag('text/plain')
    as_json = _content_type_flag('application/json')
    
    date = wz.header_property('date', read_only=False, load_func=wz.parse_date, dump_func=wz.http_date)
    etag = wz.header_property('etag', read_only=False)
    expires = wz.header_property('expires', read_only=False, load_func=wz.parse_date, dump_func=wz.http_date)
    last_modified = wz.header_property('last_modified', read_only=False, load_func=wz.parse_date, dump_func=wz.http_date)
    location = wz.header_property('location', read_only=False)

    cache_control = _autoupdate_header(name='cache_control', load_func=lambda x, on_update: wz.parse_cache_control_header(x, on_update, wz.ResponseCacheControl))
    www_authenticate = _autoupdate_header(name='www_authenticate', load_func=wz.parse_www_authenticate_header)
    
    
    @property
    def _content_disposition(self):
        cdisp = self.headers.get('content-disposition')
        if cdisp:
            return wz.parse_options_header(cdisp)
        return cdisp, None
        
    @property
    def filename(self):
        cdisp, opts = self._content_disposition
        if cdisp is not None and cdisp.lower() == 'attachment':
            return opts.get('filename')
    
    @filename.setter
    def filename(self, value):
        cdisp, opts = self._content_disposition
        if cdisp is None or cdisp.lower() == 'attachment':
            if value is not None:
                self.headers['content-disposition'] = dump_options_header('attachment', {'filename': value})
            else:
                self.headers.discard('content-disposition')
        else:
            raise ValueError('cant set filename for disposition %r' % cdisp)
        
    @property
    def content_type(self):
        raw = self.headers.get('Content-Type')
        if raw:
            return wz.parse_options_header(raw)[0]
    
    @content_type.setter
    def content_type(self, ctype):
        if ctype is None:
            self.headers.discard('Content-Type')
        elif self._charset is not None:
            self.headers['Content-Type'] = wzutil.get_content_type(ctype, self._charset)
        else:
            self.headers['Content-Type'] = ctype
    
    @property
    def charset(self):
        return self._charset
    
    @charset.setter
    def charset(self, value):
        self._charset = value
        # Need to trigger rebuilding the header.
        if 'Content-Type' in self.headers:
            self.content_type = self.content_type
    
    @property
    def status(self):
        return self._status
    
    @status.setter
    def status(self, value):
        self._status = resolve_status(value)

    
    def build_headers(self, headers=None, exc_info=None, plain=None,
        html=None, **kwargs):
        """Start the wsgi return sequence.

        If called with status, that status is resolved. If status is None, we
        use the internal status.

        If headers are supplied, they are sent after those that have been
        added to self.headers.

        """
        # Deal with content-type overrides and properties.
        if plain or html:
            log.warning('Response.start html/plain kwargs are depreciated')
            if html:
                self.content_type = 'text/html'
            else:
                self.content_type = 'text/plain'
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError('no request attribute %r' % k)
            setattr(self, k, v)
        headers = self.headers.allitems() + (list(headers) if headers is not None else [])
        headers.extend(self.cookies.build_headers())
        return headers
        
        
    def start(self, status=None, *args, **kwargs):
        """Start the wsgi return sequence.

        If called with status, that status is resolved. If status is None, we
        use the internal status.

        If headers are supplied, they are sent after those that have been
        added to self.headers.

        """
        if not self.wsgi_start:
            raise ValueError('no WSGI start')
        headers = self.build_headers(*args, **kwargs)
        if status:
            self.status = status
        self.wsgi_start(self.status, headers)



class RequestMiddleware(object):
    
    request_class = None
    
    def __init__(self, app):
        self.app = app
    
    def get_request_pair(self, environ, start):
        request = (self.request_class or Request)(environ, start)
        return request, request.response
    
    def __call__(self, environ, start):
        return self.app(*self.get_request_pair(environ, start))
    
    def __get__(self, instance, owner):
        if not instance:
            return self
        return lambda environ, start: self.app(instance, *self.get_request_pair(environ, start))


as_request = RequestMiddleware






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
    import nose; nose.run(defaultTest=__name__)

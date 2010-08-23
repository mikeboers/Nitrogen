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
from .webio import body
from .route.core import get_route_history, get_route_data


log = logging.getLogger(__name__)


def _environ_parser(func, *args, **kwargs):
    def parser(self):
        return func(self.environ, *args, **kwargs)
    return property(parser)

def _environ_property(key, load_func=None, default=None):
    if load_func:
        @property
        def _property(self):
            return load_func(self.environ.get(key, default))
    else:
        @property
        def _property(self):
            return self.environ.get(key, default)
    return _property
        

class CommonCore(object):
    
    cookie_factory = None
    
    @classmethod
    def build_class(cls, name, extra_bases=(), **namespace):
    	return type(name, (cls, ) + extra_bases, namespace)


class Request(CommonCore):
    
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
    
    def __init__(self, environ, charset=None, decode_errors=None):
        self.environ = environ
        self.charset = charset
        self.decode_errors = decode_errors
    
    method = _environ_property('REQUEST_METHOD', load_func=str.upper)
    is_get = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'GET')
    is_post = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'POST')
    is_put = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'PUT')
    is_delete = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'DELETE')
    is_head = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'HEAD')
    
    def assert_body_cache(self):
        body.assert_body_cache(self.environ)
    
    def rewind_body_cache(self):
        body.rewind_body_cache(self.environ)
    
    @wz.cached_property
    def headers(self):
        return EnvironHeaders(self.environ)
    
    query_string = _environ_property('QUERY_STRING')
    @property
    def query(self):
        return parse_query(self.environ, charset=self.charset, errors=self.decode_errors)
    get = query # Depricated.
    
    @wz.cached_property
    def cookies(self):
        raw = cookies.parse_cookies(self.environ, factory=self.cookie_factory, charset=self.charset, decode_errors=self.decode_errors)
        # This is immutable, because it does not reflect back to the environ at this time.
        return MultiMap((k, c.value) for k, c in raw.iterallitems())
    
    @property
    def stream(self):
        return body.parse_stream(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
        
    @property
    def post(self):
        return body.parse_post(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
    form = post # For Werkzeug's sake.
        
    @property
    def files(self):
        return body.parse_files(self.environ,
            charset=self.charset,
            errors=self.decode_errors,
            stream_factory=self.stream_factory,
            max_content_length=self.max_content_length,
            max_form_memory_size=self.max_form_memory_size,
        )
    
    session = _environ_property('beaker.session')
    
    @property
    def route_history(self):
        return get_route_history(self.environ)
    
    @property
    def url_for(self):
        return self.route_history.url_for
    
    @property
    def unrouted(self):
        return self.route_history[-1].path
    
    route = _environ_property('wsgiorg.routing_args', load_func=lambda x: x[1])    
    
    body = _environ_property('wsgi.input')
    
    # This one gets a little more attension because IE 6 will send us the
    # length of the previous request as an option to this header
    if_modified_since = _environ_property('HTTP_IF_MODIFIED_SINCE',
        load_func=lambda x: wz.parse_date(wz.parse_options_header(x)[0]))
    if_unmodified_since = _environ_property('HTTP_IF_UNMODIFIED_SINCE',
        load_func=lambda x: wz.parse_date(wz.parse_options_header(x)[0]))
    
    # Lots of pretty generic headers...
    accept = _environ_property('HTTP_ACCEPT',
        load_func=lambda x: wz.parse_accept_header(x, wz.MIMEAccept))
    accept_charset = _environ_property('HTTP_ACCEPT_CHARSET',
        load_func=lambda x: wz.parse_accept_header(x, wz.CharsetAccept))
    accept_encoding = _environ_property('HTTP_ACCEPT_ENCODING',
        load_func=lambda x: wz.parse_accept_header(x, wz.Accept))
    accept_language = _environ_property('HTTP_ACCEPT_LANGUAGE',
        load_func=lambda x: wz.parse_accept_header(x, wz.LanguageAccept))
    authorization = _environ_property('HTTP_AUTHORIZATION',
        load_func=wz.parse_authorization_header) # This will be None for no header.
    cache_control = _environ_property('HTTP_CACHE_CONTROL',
        load_func=wz.parse_cache_control_header)
    date = _environ_property('HTTP_DATE', load_func=wz.parse_date)
    host = _environ_property('HTTP_HOST')
    
    if_match = _environ_property('HTTP_IF_MATCH', load_func=wz.parse_etags)
    if_none_match = _environ_property('HTTP_IF_NONE_MATCH', load_func=wz.parse_etags)
    
    path_info = _environ_property('PATH_INFO')
    script_name = _environ_property('SCRIPT_NAME')
    
    referer = _environ_property('HTTP_REFERER')
    
    remote_addr = _environ_property('REMOTE_ADDR')
    remote_port = _environ_property('REMOTE_PORT', load_func=int)
    remote_user = _environ_property('REMOTE_USER')
    
    user_agent = _environ_parser(wz.UserAgent)
    
    # WSGI stuff
    is_secure = _environ_property('wsgi.url_scheme', load_func=lambda x: x == 'https')
    is_multiprocess = _environ_property('wsgi.multiprocess')
    is_multithread = _environ_property('wsgi.multithread')
    is_run_once = _environ_property('wsgi.run_once')

    # Not sent by every library, but atleast jQuery, prototype and Mochikit
    # and probably some more.
    is_xhr  = _environ_property('HTTP_X_REQUESTED_WITH', load_func=lambda x: x.lower() == 'xmlhttprequest', default='')
    is_ajax = is_xhr





def _mimetype_flag(spec):
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


class Response(CommonCore):
    
    """HTTP response abstraction.
    
    Need to pass the request this is connected to if you want to use the maybe
    pre-build response cookies container."""
    
    # The request is depricated.
    def __init__(self, body=None, status=None, headers=None, start_response=None):
        self.body = body
        self._start_response = start_response
        self.headers = headers or []
        
        if status:
            self.status = status
        else:
            self._status = '200 OK'
        
        self._charset = 'utf-8'
        if 'Content-Type' in self.headers:
            ctype, opts = wz.parse_options_header(self.headers['Content-Type'])
            self._charset = opts.get('charset')
        else:
            self.content_type = 'text/html'
    
    @wz.cached_property
    def cookies(self):
        return (self.cookie_factory or cookies.Container)()
    
    @property
    def headers(self):
        return self._headers
    
    @headers.setter
    def headers(self, value):
        self._headers = value if isinstance(value, MutableHeaders) else MutableHeaders(value)
    
    as_html = _mimetype_flag('text/html')
    as_text = _mimetype_flag('text/plain')
    as_json = _mimetype_flag('application/json')
    
    date = wz.header_property('date', read_only=False, load_func=wz.parse_date, dump_func=wz.http_date)
    
    # Should be etag object.
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

    def build_headers(self):  
        headers = self.headers.allitems()
        headers.extend(self.cookies.build_headers())
        return headers
        
    def start(self, status=None, headers=None, environ=None, start_response=None, plain=None, html=None, **kwargs):
        """Start the wsgi return sequence. DEPRICATED
        
        Can be called just like the standard start_response, but you cal also
        pass kwargs to be set as attributes before starting.
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
                raise ValueError('no response attribute %r' % k)
            setattr(self, k, v)
        
        if status is not None:
            self.status = status
        
        headers = self.build_headers() + (list(headers) if headers else [])
        (start_response or self._start_response)(status or self.status, headers)
    
    def __call__(self, body=None, status=None, headers=None, **kwargs):
        """Copy this request and set new properties to it."""
        
        copy = self.__class__(body or self.body, status or self.status, self.build_headers())
        
        for k, v in kwargs.items():
            if not hasattr(copy, k):
                raise ValueError('no response attribute %r' % k)
            setattr(copy, k, v)
        
        return copy
    
    def call_as_wsgi(self, environ, start_response):
        self.start(environ=environ, start_response=start_response)
        if isinstance(self.body, basestring):
            return [self.body]
        elif self.body:
            return self.body
        return []




class RequestMiddleware(object):
    
    request_class = None
    response_class = None
    
    def __init__(self, app):
        self.app = app
    
    @classmethod
    def _get_pair(cls, environ, start_response):
        request  = (cls.request_class  or Request )(environ)
        response = (cls.response_class or Response)(start_response=start_response)
        return request, response
    
    def _handle_response(self, environ, start, response):
        if isinstance(response, Response):
            response = response.call_as_wsgi(environ, start)
        if isinstance(response, basestring):
            start('200 OK', [])
            response = [response]
        return response
    
    def __call__(self, environ, start):
        return self._handle_response(
            environ,
            start,
            self.app(*self._get_pair(environ, start))
        )
    
    def __get__(self, instance, owner):
        if not instance:
            return self
        return lambda environ, start: self._handle_response(
            environ,
            start,
            self.app(instance, *self._get_pair(environ, start))
        )

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

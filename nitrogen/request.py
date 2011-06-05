"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""

import logging
import functools

import werkzeug as wz
import werkzeug.utils as wzutil

from multimap import MultiMap
from webstar.core import Route, get_route_data

from . import body
from . import cookies
from .uri import query

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


class Request(CommonCore, wz.Request):
    
    """WSGI/HTTP request abstraction class.
    
    This is an extension of the Werkzeug Request class. I strongly feel that
    there are a couple of things that it does not do optimally, and so I am
    making those few changes here.
    
    Also, there are a couple changes to make this backwards compatible with my
    own Request class, but those are depricated and noted where appropriate.
    
    """
    
    @classmethod
    def application(cls, func=None, add_etag=None, conditional=True):
        """Decorator to adapt WSGI to a request/response model.
        
        The function is passed a Request object, and must return a Response
        object.
        
        Params:
            add_etags: Generate an etag? None implies adding an etag if one
                does not already exist, and the response is not cached.
            conditional: Add a date header if not set, and return a 304 if
                the response does not appear modified.
        
        """
        
        if func is None:
            return functools.partial(cls.application,
                add_etags=add_etags,
                conditional=conditional,
            )
        
        add_etag = None if add_etag is None else bool(add_etag)
        
        @functools.wraps(func)
        def _wrapped(*args):
            environ = args[-2]
            request = cls(environ)
            
            response = func(*(args[:-2] + (request, )))
            
            if response.status_code == 200:
                if add_etag or add_etag is None and response.is_sequence:
                    response.add_etag()
                if conditional:
                    response.make_conditional(environ)
            
            return response(*args[-2:])
        
        return _wrapped
        
        
    # Set a default max request length. This applied to both form data, and
    # file uploads. See http://werkzeug.pocoo.org/documentation/0.6/http.html#werkzeug.parse_form_data
    # for more info.
    max_content_length = 2 * 1024 * 1028
    
    # Function to use to create file objects at parse time. Defaults to
    # rejecting all files. There are more supplied in nitrogen.body.
    # See http://werkzeug.pocoo.org/documentation/0.6/http.html#werkzeug.parse_form_data
    # for more info.
    stream_factory = body.reject_factory
    
    # Using my multiple-value-per-key mapping, as it retains more ordering
    # information.
    parameter_storage_class = MultiMap
    
    # Properties for quick method testing. Depricated.
    is_get = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'GET')
    is_post = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'POST')
    is_put = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'PUT')
    is_delete = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'DELETE')
    is_head = _environ_property('REQUEST_METHOD', load_func=lambda x: x.upper() == 'HEAD')
    
    def _get_file_stream(self, total_content_length, content_type, filename=None,
        content_length=None):
        """Called to get a stream for the file upload.
        
        This must provide a file-like class with `read()`, `readline()`
        and `seek()` methods that is both writeable and readable.
        
        The default implementation calls self.stream_factory with the given
        arguments and wraps it in a webio.body.FileWrapper (to track the
        amount written).
        
        The default self.stream_factory raises an exception (ie. does not
        allow file uploads).
        
        """
        
        return body.FileWrapper(
            self.stream_factory, 
            total_content_length,
            content_type,
            filename,
            content_length,
        )
    
    # I am supplying this synonym for the Werkzeug property simply for
    # backwards compatibility.
    post = wz.Request.form
    
    @wz.cached_property
    def query(self):
        return query.FrozenQuery.from_environ(self.environ, charset=self.charset, decode_errors=self.encoding_errors)
    args = query # Werkzeug's name.
    
    # My cookies are much nicer. 
    raw_cookies = _environ_property('HTTP_COOKIE')
    @wz.cached_property
    def cookies(self):
        raw = self.cookie_factory(self.raw_cookies,
            charset=self.charset,
            decode_errors=self.encoding_errors
        )
        # Throw it into an immutable container.
        return MultiMap((k, c.value) for k, c in raw.iterallitems())
    
    body = _environ_property('wsgi.input')
    
    def assert_body_cache(self):
        body.assert_body_cache(self.environ)
    
    # Depricated. Use request.body.seek(0) after caching it.
    def rewind_body_cache(self):
        body.rewind_body_cache(self.environ)
    
    session = _environ_property('beaker.session')
    
    @property
    def route_history(self):
        return Route.from_environ(self.environ)
    
    @property
    def url_for(self):
        return self.route_history.url_for
    
    @property
    def unrouted(self):
        return self.route_history[-1].unrouted
    
    route = _environ_property('wsgiorg.routing_args', load_func=lambda x: x[1])    
    
    # These get a little more attension because Netscape extended HTTP/1.0 to
    # add the length of the previous request as an option to this header. IE 6
    # does this too.
    if_modified_since = _environ_property('HTTP_IF_MODIFIED_SINCE',
        load_func=lambda x: wz.parse_date((x or '').split(';', 1)[0]))
    if_unmodified_since = _environ_property('HTTP_IF_UNMODIFIED_SINCE',
        load_func=lambda x: wz.parse_date((x or '').split(';', 1)[0]))
    
    # Depricated.
    etag = _environ_property('HTTP_IF_NOT_MATCH')
    
    # Werkzeug supplies referrer, which is the correct spelling, but I want
    # this here for completeness.
    referer = wz.Request.referrer
        
    # Werkzeug only supplied the remote_addr.
    remote_port = _environ_property('REMOTE_PORT', load_func=int)
    
    # Werkzeug supplies host, which includes the port if supplied.
    hostname = _environ_property('HTTP_HOST')
        
    # Werkzeug does not supply these most basic of headers (likely because it
    # has much better high-level ones).
    path_info = _environ_property('PATH_INFO')
    script_name = _environ_property('SCRIPT_NAME')
    
    # Synonym. Likely better to use the original.
    is_ajax = wz.Request.is_xhr





def _mimetype_flag(spec):
    """Build a property for quick setting of content types.
    
    You can only set these properties to be True. When you do so, the content-
    type of the response is set to the type specified by `spec`.
    
    """
    
    @property
    def prop(self):
        return self.mimetype == spec
    @prop.setter
    def prop(self, value):
        if not value:
            raise ValueError('cannot be set to non-true value')        
        self.mimetype = spec
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


class Response(CommonCore, wz.Response):
    
    """WSGI/HTTP response abstraction.
    
    This is an extension of the Werkzeug Response class. I strongly feel that
    there are a couple of things that it does not do optimally, and so I am
    making those few changes here.
    
    Also, there are a couple changes to make this backwards compatible with my
    own Response class, but those are depricated and noted where appropriate.
    
    See the docs for Werkzeug's Response class.
    
    """
    
    def __init__(self, response=None, status=None, headers=None, **kwargs):
        
        super_kwargs = {}
        for name in 'mimetype', 'content_type', 'direct_passthrough':
            super_kwargs[name] = kwargs.pop(name, None)
        super(Response, self).__init__(response, status, headers, **super_kwargs)
        
        self._wsgi_start = kwargs.pop('start_response', None) or kwargs.pop('start', None)
        
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError('no response attribute %r' % k)
            setattr(self, k, v)
        
        
    
    @wz.cached_property
    def cookies(self):
        return (self.cookie_factory or cookies.Container)()
    
    def set_cookie(self, *args, **kwargs):
        self.cookies.set(*args, **kwargs)
    
    def expire_cookie(self, *args, **kwargs):
        self.cookies.expire(*args, **kwargs)
    delete_cookie = expire_cookie
    
    # Depricated. Set mimetype directly instead.
    as_html = _mimetype_flag('text/html')
    as_text = _mimetype_flag('text/plain')
    as_json = _mimetype_flag('application/json')
    
    # Depricated. Use set_etag or add_etag instead.
    etag = wz.header_property('etag', read_only=False)
    
    def get_wsgi_headers(self, environ):
        headers = super(Response, self).get_wsgi_headers(environ)
        headers.extend(self.cookies.build_headers())
        return headers
    
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
                self.headers['content-disposition'] = wz.dump_options_header('attachment', {'filename': value})
            else:
                self.headers.discard('content-disposition')
        else:
            raise ValueError('cant set filename for disposition %r' % cdisp)
        
    def start(self, status=None, headers=None, start=None, plain=None, html=None, **kwargs):
        """Start the wsgi return sequence. DEPRICATED
        
        Can be called just like the standard start_response, but you can also
        pass kwargs to be set as attributes before starting.
        """
        
        # Deal with content-type overrides and properties.
        if plain or html:
            log.warning('Response.start html/plain kwargs are depreciated')
            if html:
                self.mimetype = 'text/html'
            else:
                self.mimetype = 'text/plain'
        
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError('no response attribute %r' % k)
            setattr(self, k, v)
        
        if isinstance(status, int):
            self.status_code = status
        elif status:
            self.status = status
        
        headers = self.headers.to_list(self.charset) + self.cookies.build_headers() + (list(headers) if headers else [])
        (start or self._wsgi_start)(self.status, headers)
    
    def redirect(self, location, status=303, **kwargs):
        self.start(status, location=location, **kwargs)


class RequestMiddleware(object):
    
    request_class = None
    response_class = None
    
    def __init__(self, app):
        self.app = app
    
    @classmethod
    def _get_pair(cls, environ, start_response):
        request  = (cls.request_class  or Request )(environ)
        response = (cls.response_class or Response)(start=start_response)
        return request, response
    
    def _handle_response(self, environ, start_response, response):
        if isinstance(response, Response):
            iter, status, headers = response.get_wsgi_response(environ)
            start_response(status, headers)
            response = iter
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




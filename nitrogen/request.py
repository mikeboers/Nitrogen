"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""

import logging
import functools
import hashlib
import os
import mimetypes
import time

import werkzeug as wz
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.http
import werkzeug.wsgi
import werkzeug.datastructures

from multimap import MultiMap
from webstar.core import Route, get_route_data

from . import body
from . import cookies
from .uri import query

log = logging.getLogger(__name__)






class Request(wz.wrappers.Request):
    
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
    
    # I prefer this name.
    post = wz.wrappers.Request.form
    
    @wz.utils.cached_property
    def query(self):
        return query.FrozenQuery.from_environ(self.environ, charset=self.charset, decode_errors=self.encoding_errors)
    args = query # Werkzeug's name.
    
    # My cookies are much nicer. 
    cookie_string = wz.utils.environ_property('HTTP_COOKIE')
    cookie_factory = cookies.Container
    @wz.utils.cached_property
    def cookies(self):
        raw = self.cookie_factory(self.cookie_string,
            charset=self.charset,
            decode_errors=self.encoding_errors
        )
        # Throw it into an immutable container.
        return MultiMap((k, c.value) for k, c in raw.iterallitems())
    
    session = wz.utils.environ_property('beaker.session')
    
    @property
    def route_history(self):
        return Route.from_environ(self.environ)
    
    @property
    def url_for(self):
        return self.route_history.url_for
    
    @property
    def unrouted(self):
        return self.route_history[-1].unrouted
    
    route = wz.utils.environ_property('wsgiorg.routing_args', load_func=lambda x: x[1])
    
    # Werkzeug supplies if_none_match, which is likely better.
    etag = wz.utils.environ_property('HTTP_IF_NOT_MATCH')







class Response(wz.wrappers.Response):
    
    """WSGI/HTTP response abstraction.
    
    This is an extension of the Werkzeug Response class. I strongly feel that
    there are a couple of things that it does not do optimally, and so I am
    making those few changes here.
    
    Also, there are a couple changes to make this backwards compatible with my
    own Response class, but those are depricated and noted where appropriate.
    
    See the docs for Werkzeug's Response class.
    
    """
    
    default_mimetype = 'text/html'
    
    def __init__(self, response=None, status=None, headers=None, **kwargs):
        
        # Pull out all the args that would normally be passed to werkzeug's
        # Response constructor.
        super_kwargs = {}
        for name in 'mimetype', 'content_type', 'direct_passthrough':
            super_kwargs[name] = kwargs.pop(name, None)
        super(Response, self).__init__(response, status, headers, **super_kwargs)
        
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError('no response attribute %r' % k)
            setattr(self, k, v)
        
        
    cookie_factory = cookies.Container
    @wz.utils.cached_property
    def cookies(self):
        return self.cookie_factory()
    
    def set_cookie(self, *args, **kwargs):
        self.cookies.set(*args, **kwargs)
    
    def expire_cookie(self, *args, **kwargs):
        self.cookies.expire(*args, **kwargs)
    delete_cookie = expire_cookie
    
    # Depricated. Use set_etag or add_etag instead.
    etag = wz.utils.header_property('etag', read_only=False)
    
    def get_wsgi_headers(self, environ):
        headers = super(Response, self).get_wsgi_headers(environ)
        
        # Our cookies are better.
        headers.extend(self.cookies.build_headers())
        
        # Some servers can't deal with X-Sendfile if not 200.
        if (100 <= self.status_code < 200 or
            self.status_code == 204 or
            300 <= self.status_code < 400
        ):
            headers.pop('X-Sendfile', None)
        
        return headers
    
    @property
    def _content_disposition(self):
        cdisp = self.headers.get('content-disposition')
        if cdisp:
            return wz.http.parse_options_header(cdisp)
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
                self.headers['content-disposition'] = wz.http.dump_options_header('attachment', {'filename': value})
            else:
                self.headers.discard('content-disposition')
        else:
            raise ValueError('cant set filename for disposition %r' % cdisp)

    
    use_x_sendfile = True
    
    def send_file(self, filename, mimetype=None, as_attachment=False,
        attachment_filename=None, add_etags=None, cache_max_age=60 * 60 * 12,
    ):
        """Lifted from flask.
        
        Mimetype is pulled from filename if not given. Attachment filename is
        the basename of the filename if not given. Uses X-Sendfile if
        Response.use_x_sendfile is True (default). If add_etags is None will
        add an etag if there isn't one already set. cache_max_age also sets
        cache_control.expires.
        
        Uses a generic werkzeug.FileWrapper instead of what is availible in
        the environment. Also pulled out all conditional code.
        """
        
        filename  = os.path.abspath(filename)
        
        if mimetype is None and (filename or attachment_filename):
            mimetype = mimetypes.guess_type(filename or attachment_filename)[0]
        if mimetype is None:
            mimetype = 'application/octet-stream'

        if as_attachment:
            self.filename = attachment_filename or os.path.basename(filename)

        if self.use_x_sendfile and filename:
            self.headers['X-Sendfile'] = filename
            data = None
        else:
            file = open(filename, 'rb')
            data = wz.wsgi.FileWrapper(file)

        mtime = os.path.getmtime(filename)
        self.mimetype = mimetype
        self.direct_passthrough = True
        self.last_modified = mtime


        self.cache_control.public = True
        if cache_max_age:
            self.cache_control.max_age = cache_max_age
            self.expires = int(time.time() + cache_max_age)

        if add_etags or add_etags is None and 'etag' not in self.headers:
            self.set_etag('sendfile-%s-%s-%s' % (
                mtime,
                os.path.getsize(filename),
                hashlib.md5(
                    filename.encode('utf8') if isinstance(filename, unicode)
                    else filename
                ).hexdigest()[:8]
            ))

        return self




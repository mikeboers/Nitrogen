"""Module for WSGI request adapter.

This class is designed to raise the level of abstraction much higher than
just environ and start, and provide get, post, files, cookies, session,
routing, etc.

"""

from cStringIO import StringIO
import cStringIO as cstringio
import functools
import hashlib
import io
import logging
import mimetypes
import os
import StringIO as stringio
import time

import werkzeug as wz
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.http
import werkzeug.wsgi
import werkzeug.datastructures

from webstar.core import Route, get_route_data

from . import body
from . import cookies


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
    def auto_application(cls, func=None, **kwargs):
        
        # Work as a decorator.
        if func is None:
            return functools.partial(cls.auto_application, **kwargs)
        
        # TODO: work with unbound methods, bound methods and functools.partials.
        
        input_func = func
        if hasattr(func, '__Request_auto_application__'):
            return func.__Request_auto_application__
        try:
            if func.__code__.co_argcount == 1:
                func = cls.application(func, **kwargs)
            # elif func.__code__.co_argcount == 0:
            #     print func
            #     func = cls.application(lambda request: input_func(), **kwargs)
        except AttributeError as e:
            # methods and callable classes don't have __code__
            pass
        
        # Using the __dict__ method because instance methods don't let us set
        # attributes directly.
        input_func.__dict__['__Request_auto_application__'] = func
        return func
    
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
        
        # Work as a decorator.
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
            request.response = Response()
            
            response = func(*(args[:-2] + (request, )))
            
            # Use default response.
            if response is None:
                response = request.response
            
            if isinstance(response, tuple):
                response = Response(*response)
            elif isinstance(response, basestring):
                response = Response(response)
            
            if response.status_code == 200:
                if add_etag or add_etag is None and response.is_sequence:
                    response.add_etag()
                if conditional and response.is_sequence:
                    response.make_conditional(environ)
            
            return response(*args[-2:])
        
        return _wrapped
        
        
    # Set a default max request length. This applied to both form data, and
    # file uploads. See http://werkzeug.pocoo.org/docs/http/#werkzeug.formparser.parse_form_data
    # for more info.
    max_form_memory_size = max_content_length = 2 * 1024 * 1028
    
    # Function to use to create file objects at parse time. Defaults to
    # rejecting all files. There are more supplied in nitrogen.body.
    # See http://werkzeug.pocoo.org/docs/http/#werkzeug.formparser.parse_form_data
    # for more info.
    stream_factory = body.reject_factory
        
    def _get_file_stream(self, total_content_length, content_type, filename=None,
        content_length=None):
        """Called to get a stream for the file upload.
        
        This must provide a file-like class with `read()`, `readline()`
        and `seek()` methods that is both writeable and readable.
        
        This calls self.stream_factory with the given arguments, the default
        of which raises an exception (ie. does not allow file uploads).
        
        """
        
        return self.stream_factory(
            total_content_length,
            content_type,
            filename,
            content_length,
        )
    
    # I prefer these names.
    query = wz.wrappers.Request.args
    post = wz.wrappers.Request.form
    path_info = wz.wrappers.Request.path
    script_name = wz.wrappers.Request.script_root
    
    session = wz.utils.environ_property('beaker.session')
    
    @wz.utils.cached_property
    def body(self):
        content_length = self.headers.get('content-length', type=int)
        if content_length is not None:
            return werkzeug.wsgi.LimitedStream(self.environ['wsgi.input'], content_length)
        return self.environ['wsgi.input']
    
    def make_body_seekable(self):
        stdin = self.environ['wsgi.input']
        if not isinstance(stdin, (cstringio.InputType, io.StringIO, stringio.StringIO)):
            self.body = self.environ['wsgi.input'] = StringIO(self.body.read())
            self.body.seek(0)
        
    @property
    def route_steps(self):
        return Route.from_environ(self.environ)
        
    @property
    def url_for(self):
        return self.route_steps.url_for
    
    route = wz.utils.environ_property('wsgiorg.routing_args', load_func=lambda x: x[1])
    
    # Werkzeug supplies if_none_match, which is likely better.
    etag = wz.utils.environ_property('HTTP_IF_NONE_MATCH')

    @property
    def full_path(self):
        return '/' + (self.script_name.rstrip('/') + '/' + self.path_info.lstrip('/')).strip('/')
    
    @property
    def is_eventstream(self):
        return self.accept_mimetypes.best == 'text/event-stream'
    
    @property
    def is_websocket(self):
        return (
            self.environ.get('HTTP_UPGRADE', '').strip().lower() == 'websocket' and
            self.environ.get('HTTP_CONNECTION', '').strip().lower() == 'upgrade'
        )







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
    
    # Depricated. Use set_etag or add_etag instead.
    etag = wz.utils.header_property('etag', read_only=False)
    
    def get_wsgi_headers(self, environ):
        headers = super(Response, self).get_wsgi_headers(environ)
        
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
    
    def redirect(self, location, code=303):
        self.status_code = code
        self.location = location
        self.response = ()
        return self
    
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

    
    use_x_sendfile = 'USE_X_SENDFILE' in os.environ
    
    def send_file(self, filename, mimetype=None, as_attachment=False,
        attachment_filename=None, add_etags=None, cache_max_age=None,
        use_x_sendfile=None
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

        if (use_x_sendfile or (use_x_sendfile is None and self.use_x_sendfile)) and filename:
            self.headers['X-Sendfile'] = filename
            self.response = ()
        else:
            file = open(filename, 'rb')
            self.response = wz.wsgi.FileWrapper(file)

        mtime = os.path.getmtime(filename)
        self.mimetype = mimetype
        self.direct_passthrough = True
        self.last_modified = mtime

        self.cache_control.public = True
        if cache_max_age is not None:
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





from threading import local as _local
import logging

from werkzeug import cached_property

from . import cookies
from . import request
from . import route
from .serve import serve
from nitrogen.compress import compressor
from nitrogen.unicode import encoder


log = logging.getLogger(__name__)


class Config(dict):
    
    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            pass
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass


class Core(object):
    
    base_config = {
        'root': '',
        'run_mode': 'socket',
        'private_key_material': None,
    }
    
    def __init__(self, *args, **kwargs):
        
        # Build up the base config from all the base_configs on the mro chain,
        # along with everything supplied. This is slightly inefficient; meh.
        config = {}
        for cls in reversed(self.__class__.__mro__):
            config.update(getattr(cls, 'base_config', {}))
        for arg in args:
            print arg
            config.update(arg)
        config.update(kwargs)
        self.config = Config(config)
        
        # Need to keep track of all the thread-local objects, so we can reset
        # them for every request.
        self._locals = []
        
        # Setup initial routers. Use the primary router (or just the .route
        # method) for simple apps, or append your own router to the routers
        # list. Feel free to wrap .wsgi_app at will. It will be automatically
        # wrapped by the AppMixins at every request.
        self.primary_router = route.ReRouter()
        self.routers = route.Chain([self.primary_router])
        self.wsgi_app = self.routers
        
        # Setup middleware stack. This is a list of tuples; the second is a
        # function to call that takes a WSGI app, and returns one. The first
        # is a value (normally a tuple of ints) representing the priority;
        # lower values will be wrapped first. Canonically:
        #   (0, ): application layer.
        #   (1, ): framework layer.
        #   (2, ): transport layer.
        # Within those layers you can specialize to push closer to front or
        # end. ie.: (0, -10) will be very near the front of the app layer,
        # while (2, 10) will be at the end of the transport layer.
        #
        # Use self.register_middleware to add to this list.
        self.middleware = []
        self._flattened_wsgi_app = None
        
        self.register_middleware((self.FRAMEWORK_LAYER, 0), encoder)
        self.register_middleware((self.TRANSPORT_LAYER, 1000), compressor)
        
        self._local = self.local()
        
        # Build the base Request and Response classes we will use.
        self.request_class = request.Request.build_class(
            self.__class__.__name__ + 'Request',
            (),
            cookie_factory=self.cookie_factory
        )
        self.response_class = request.Response.build_class(
            self.__class__.__name__ + 'Response',
            (),
            cookie_factory=self.cookie_factory
        )
    
    APP_LAYER = 0
    FRAMEWORK_LAYER = 1
    TRANSPORT_LAYER = 2
    
    def register_middleware(self, priority, func, args=None, kwargs=None):
        if isinstance(priority, (int, float)):
            priority = (priority, )
        if not isinstance(priority, tuple):
            raise TypeError('priority must be a tuple; got %s %r' % (type(priority), priority))
        self.middleware.append((priority, func, args or (), kwargs or {}))    
    
    def _call_wsgi_app(self, environ, start):
        return self.wsgi_app(environ, start)
    
    def flatten_middleware(self):
        middleware = sorted(self.middleware)
        log.debug('Flattening middleware:')
        app = self._call_wsgi_app
        for priority, func, args, kwargs in middleware:
            log.debug('%12r: %s' % (priority, func))
            app = func(app, *args, **kwargs)
        self._flattened_wsgi_app = app
        
    def cookie_factory(self, *args, **kwargs):
        if self.config.private_key_material:
            return cookies.SignedContainer(self.config.private_key_material, *args, **kwargs)
        return cookies.Container(*args, **kwargs)
        
    @property
    def route(self):
        return self.primary_router.register
    
    @property
    def url_for(self):
        return self.routers.url_for
    
    def local(self):
        """Return a managed thread-local object, reset for every request.
        
        This is nessesary to make sure that thread re-use does not poison our
        local objects (which we assume to be clean every time).
        
        """
        obj = _local()
        self._locals.append(obj)
        return obj
    
    def _clear_locals(self):
        """Clear out all the thread-local objects that we control.
        
        This will be run before every request.
        
        """
        for obj in self._locals:
            obj.__dict__.clear()
    
    @property
    def request(self):
        return self._local.request
    
    @property
    def environ(self):
        return self._local.environ
    
    def init_request(self, environ):
        self._clear_locals()
        self._local.environ = environ
        self._local.request = self.request_class(environ)
    
    def _auto_flatten_middleware(self):
        if not self._flattened_wsgi_app:
            self.flatten_middleware()
        return self._flattened_wsgi_app
        
    def __call__(self, environ, start):
        app = self._auto_flatten_middleware()
        self.init_request(environ)
        return app(environ, start)
    
    def run(self, mode=None, *args, **kwargs):
        self._auto_flatten_middleware()
        serve(mode or self.config['run_mode'], self, *args, **kwargs)


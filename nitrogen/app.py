
import logging

from werkzeug import cached_property

from . import cookies
from . import local
from . import request
from . import route
from .compress import compressor
from .proxy import Proxy
from .serve import serve
from .serve.fcgi import reloader
from .unicode import encoder

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
    
    def setdefaults(self, **kwargs):
        results = {}
        for name, default in kwargs.iteritems():
            results[name] = self.setdefault(name, default)
        return results
            


def build_inheritance_mixin_class(parent_class, base, name=None):
    """Make a class from mixins in the inheritence chain of a parent class.
    
    Works backwards down the MRO of a parent class, collecting unique mixin
    classes named after the base object. Eg. if extending a Request class, this
    will look for RequestMixin classes.
    
    """
    name = name or base.__name__
    bases = []
    for cls in parent_class.__mro__:
        mixin = getattr(cls, name + 'Mixin', None)
        if mixin and mixin not in bases:
            bases.append(mixin)
    bases.append(base)
    cls = type(parent_class.__class__.__name__ + name, tuple(bases), {})
    return cls


class Core(object):
    
    def __init__(self, *args, **kwargs):
        
        self.config = Config(kwargs)
        self.setup_config()
        
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
        
        if self.config.reload:
            self.register_middleware((self.TRANSPORT_LAYER, 10000), reloader, (self.config.reloader_packages, ))
        
        self._local = self.local()
        self.request = self._local('request')
        
        Core.RequestMixin.cookie_factory = self.cookie_factory
        Core.ResponseMixin.cookie_factory = self.cookie_factory
        
    def setup_config(self):
        self.config.setdefaults(
            root='',
            runmode='socket',
            private_key=None,
            reload=False,
            reloader_packages=('nitrogen', 'app'),
        )
    
    # These are stubs for us to add on to in the __init__ method.
    class RequestMixin(object): pass
    class ResponseMixin(object): pass
    
    build_request_class = lambda self: build_inheritance_mixin_class(self.__class__, request.Request)
    Request = cached_property(build_request_class, name='Request')
    
    build_response_class = lambda self: build_inheritance_mixin_class(self.__class__, request.Response)
    Response = cached_property(build_response_class, name='Response')
    
    def export_to(self, map):
        map.update(
            Request=self.Request,
            Response=self.Response,
            route=self.route,
            request=self.request,
        )
    
    APPLICATION_LAYER = 0
    FRAMEWORK_LAYER = 1
    TRANSPORT_LAYER = 2
    
    def register_middleware(self, priority, func, args=None, kwargs=None):
        self._flattened_wsgi_app = None
        if isinstance(priority, (int, float)):
            priority = (priority, )
        if not isinstance(priority, tuple):
            raise TypeError('priority must be a tuple; got %s %r' % (type(priority), priority))
        self.middleware.append((priority, func, args or (), kwargs or {}))    
    
    def _call_wsgi_app(self, environ, start):
        return self.wsgi_app(environ, start)
    
    def flatten_middleware(self):
        if self._flattened_wsgi_app is None:
            middleware = sorted(self.middleware)
            log.debug('Flattening middleware:')
            app = self._call_wsgi_app
            for priority, func, args, kwargs in middleware:
                log.debug('%12r: %s' % (priority, func))
                app = func(app, *args, **kwargs)
            self._flattened_wsgi_app = app
        return self._flattened_wsgi_app
        
        
    def cookie_factory(self, *args, **kwargs):
        if self.config.private_key:
            return cookies.SignedContainer(self.config.private_key, *args, **kwargs)
        return cookies.Container(*args, **kwargs)
        
    @property
    def route(self):
        return self.primary_router.register
    
    @property
    def url_for(self):
        return self.routers.url_for
    
    @property
    def local_manager(self):
        # This is a property so we can access it without calling __init__
        self.__dict__['local_mananger'] = obj = local.LocalManager()
        return obj
    
    def local(self):
        """Return a managed thread-local object, reset for every request.
        
        This is nessesary to make sure that thread re-use does not poison our
        local objects (which we assume to be clean every time).
        
        """
        obj = self.local_manager.local()
        self.__dict__.setdefault('_locals', []).append(obj)
        return obj
    
    def init_request(self, environ):
        self._local.request = self.Request(environ)
    
    def finish_request(self):
        self.local_manager.cleanup()
        
    def __call__(self, environ, start):
        app = self.flatten_middleware()
        self.init_request(environ)
        try:
            for x in app(environ, start):
                yield x
        finally:
            self.finish_request()
    
    def run(self, mode=None, *args, **kwargs):
        self.flatten_middleware()
        serve(mode or self.config['run_mode'], self, *args, **kwargs)


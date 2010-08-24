
from threading import local as _local

from werkzeug import cached_property

from . import cookies
from . import request
from . import route
from .serve import serve
from nitrogen.compress import compressor
from nitrogen.http.status import not_found_catcher, catch_any_status
from nitrogen.unicode import encoder

class ConfigKeyError(KeyError):
    pass

class Config(dict):
    
    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            raise ConfigKeyError(name)
    
    # def __getattribute__(self, name):
    #     try:
    #         return self[name]
    #     except KeyError:
    #         pass


class Core(object):
    
    base_config = {
        'root': '',
        'run_mode': 'socket',
        'private_key': None,
    }
    
    def __init__(self, *args, **kwargs):
        
        # Build up the base config from all the base_configs on the mro chain.
        config = {}
        applied = set()
        for cls in reversed(self.__class__.__mro__):
            base = getattr(cls, 'base_config', None)
            if base and id(base) not in applied:
                config.update(base)
                applied.add(id(base))
        config.update(kwargs)
        self.config = Config(config)
        
        # Need to keep track of all the thread-local objects, so we can reset
        # them for every request.
        self._locals = []
        
        # Setup primary routers.
        self.primary_router = route.ReRouter()
        self.routers = route.Chain([self.primary_router])
        
        # First level of middleware wrapping.
        app = self.routers
        app = self.wrap_wsgi_application(app)
        app = self.wrap_wsgi_framework(app)
        app = self.wrap_wsgi_transport(app)
        self.wsgi_app = app
        
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
    
    def wrap_wsgi_application(self, app):
        return app
    
    def wrap_wsgi_framework(self, app):
        app = encoder(app)
        app = catch_any_status(app)
        # log/handle errors here
        return app
    
    def wrap_wsgi_transport(self, app):    
        app = compressor(app)
        return app
        
    
    def cookie_factory(self, *args, **kwargs):
        if self.config.get('private_key'):
            return cookies.SignedContainer(self.config['private_key'], *args, **kwargs)
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
        
    def __call__(self, environ, start):
        self.init_request(environ)
        return self.wsgi_app(environ, start)
    
    def run(self, mode=None, *args, **kwargs):
        serve(mode or self.config['run_mode'], self, *args, **kwargs)


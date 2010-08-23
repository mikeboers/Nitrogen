
from threading import local as _local

from werkzeug import cached_property

from . import route
from . import request
from .webio import cookies
from .wsgi.server import serve
from nitrogen.http.encode import compressor
from nitrogen.http.status import not_found_catcher, catch_any_status

class ConfigKeyError(KeyError):
    pass

class Config(dict):
    
    def __getitem__(self, name):
        try:
            return dict.__getitem__(self, name)
        except KeyError:
            raise ConfigKeyError(name)


class Core(object):
    
    base_config = {
        'run_mode': 'socket',
    }
    
    cookie_factory = None
    
    def __init__(self, *args, **kwargs):
        
        # Build up the base config from all the base_configs on the mro chain.
        self.config = Config(**kwargs)
        applied = set()
        for cls in reversed(self.__class__.__mro__):
            base = getattr(cls, 'base_config', None)
            if base and id(base) not in applied:
                self.config.update(base)
                applied.add(id(base))
        
        self._locals = []
        
        # Setup primary routers.
        self._rerouter = route.ReRouter()
        self.routers = route.Chain([self._rerouter])
        
        # First level of middleware wrapping.
        app = self.routers
        # app = not_found_catcher(app) # Ideally this will be changed into a more abstract version.
        app = catch_any_status(app)
        self.wsgi_app = app
        
        self.__is_setup = False
        self._local = self.local()
    
    @cached_property
    def route(self):
        return self._rerouter.register
    
    @cached_property
    def url_for(self):
        return self.routers.url_for
    
    def local(self):
        obj = _local()
        self._locals.append(obj)
        return obj
    
    def _clear_locals(self):
        for obj in self._locals:
            obj.__dict__.clear()
    
    def setup(self):
        if not self.cookie_factory:
            if 'private_key' in self.config:
                self.cookie_factory = cookies.SignedContainer.make_factory(self.config['private_key'])
            else:
                self.cookie_factory = cookies.Container
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
        self.as_request = type(
            self.__class__.__name__ + 'RequestMiddleware',
            (request.RequestMiddleware, ),
            dict(
                request_class=self.request_class,
                response_class=self.response_class,
            )
        )
        
        # Do whatever middleware wrapping we need to do.
        app = self.wsgi_app
        app = compressor(app)
        self._wsgi_app = app
    
    @property
    def request(self):
        return self._local.request
    
    def init_request(self, environ):
        if not self.__is_setup:
            self.setup()
            self.__is_setup = True
        self._clear_locals()
        self._local.environ = environ
        self._local.request = self.request_class(environ)
        
    def __call__(self, environ, start):
        self.init_request(environ)
        return self._wsgi_app(environ, start)
    
    def run(self, mode=None, *args, **kwargs):
        serve(mode or self.config['run_mode'], self, *args, **kwargs)


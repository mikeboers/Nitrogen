
import logging
import os
import threading

import werkzeug as wz
import werkzeug.wrappers

import webstar

from . import config
from . import request
from . import status
from . import mixin
from .event import instance_event
from .static import StaticRouter


__all__ = ['App']
log = logging.getLogger(__name__)


class Core(object):
        
    before_request = instance_event('before_request')
    on_wsgi_start = instance_event('on_wsgi_start')
    after_request = instance_event('after_request')
    
    
    def __init__(self, *args, **kwargs):
        
        self.config = config.Config()
        for arg in args:
            self.config.update(arg)
        self.config.update(kwargs)
        self.setup_config()
        
        # Setup initial routers. Use the primary router (or just the .route
        # method) for simple apps, or append your own router to the routers
        # list.
        self.router = webstar.Router()
        self.static_router = StaticRouter(**self.config.filter_prefix('static_'))
        self.router.register(None, self.static_router)
        self.router.not_found_app = self.not_found_app
        
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
        
        self._local = self.local()
        
        Core.RequestMixin.app = self
        Core.ResponseMixin.app = self
    
    def setup_config(self):
        self.config.setdefaults(
            root='',
            runmode='socket',
            private_key=None,
            reload=False,
            reloader_packages=('nitrogen', 'app'),
            static_cache_max_age=3600,
            cache_dir='/tmp',
        )
        self.config.setdefault('static_path', []).append(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/static'
        )
    
    def not_found_app(self, environ, start):
        raise status.NotFound('could not route')
    
    # These are stubs for us to add on to in the __init__ method.
    class RequestMixin(object): pass
    class ResponseMixin(object): pass
    
    Request = mixin.builder_property(request.Request)
    Response = mixin.builder_property(request.Response)
    
    def export_to(self, map):
        map.update(
            Request=self.Request,
            Response=self.Response,
            route=self.route,
            config=self.config,
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
    
    # So we can overload it to check for permissions and predicates.
    def _get_wsgi_app(self, environ):
        return self.router.wsgi_route(environ)
    
    def wsgi_app(self, environ, start):
        app = self._get_wsgi_app(environ)
        return self.Request.auto_application(app)(environ, start)
    
    def flatten_middleware(self):
        if self._flattened_wsgi_app is None:
            middleware = sorted(self.middleware)
            log.debug('Flattening middleware:')
            app = self.wsgi_app
            for priority, func, args, kwargs in middleware:
                log.debug('%12r: %s' % (priority, func))
                app = func(app, *args, **kwargs)
            self._flattened_wsgi_app = app
        return self._flattened_wsgi_app
        
    @property
    def route(self):
        return self.router.register
    
    @property
    def url_for(self):
        return self.router.url_for
    
    @wz.utils.cached_property
    def __managed_locals(self):
        return []
    
    def local(self):
        """Return a managed thread-local object, reset for every request.
        
        This is nessesary to make sure that thread re-use does not poison our
        local objects (which we assume to be clean every time).
        
        """
        obj = threading.local()
        self.__managed_locals.append(obj)
        return obj
    
    def local_request(self):
        return self.Request(self._local.environ)
    
    def __call__(self, environ, start):
        app = self.flatten_middleware()
        
        self._local.environ = environ
        self._local.request = self.local_request()
        
        self.before_request.trigger(environ)
        
        def _start(*args):
            self.on_wsgi_start.trigger(*args)
            return start(*args)
        
        try:
            for x in app(environ, _start):
                yield x
                
        finally:
            self.after_request.trigger(environ)
            for obj in self.__managed_locals:
                obj.__dict__.clear()
    
    def test_client(self, use_cookies=True):
        """Builds a test client that will call this app."""

        from . import test
        return test.Client(self, wz.wrappers.Response, use_cookies=use_cookies)



def _build_final_class():
    from .auth import AuthAppMixin
    from .crud import CRUDAppMixin
    from .exception import ExceptionAppMixin
    from .wtforms.app import FormAppMixin
    from .imgsizer import ImgSizerAppMixin
    # from .js import JavaScriptAppMixin
    from .logs import LoggingAppMixin
    from .session import SessionAppMixin
    from .sqlalchemy.app import SQLAlchemyAppMixin
    # from .textblobs import TextBlobAppMixin
    from .tracker import TrackerAppMixin
    from .view.app import ViewAppMixin
    from .cookies import CookieAppMixin

    # Be careful about the order of these.
    class App(
        ImgSizerAppMixin, # Needs View
        # TextBlobAppMixin, # Needs Form and CRUD.
        FormAppMixin, # Needs View
        CRUDAppMixin, # Needs View and SQLAlchemy
        TrackerAppMixin, # Needs View (and maybe session)
        SessionAppMixin, # Needs View (for view_globals)
        ViewAppMixin,
        SQLAlchemyAppMixin,
        AuthAppMixin,
        CookieAppMixin,
        LoggingAppMixin,
        ExceptionAppMixin, # Must be after anything that may throw exceptions.
        Core
    ):
        pass
        
    return App


App = _build_final_class()
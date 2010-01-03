

from nitrogen.route.rerouter import ReRouter
from .environ import UserContext
from ..model.environ import ModelContext
from ..view.environ import ViewContext

class UserController(object):
    
    def __init__(self, user_environ, view_environ):
        self.user_environ = user_environ
        self.view_environ = view_environ
        self._setup_router()
    
    def __getattr__(self, name):
        for x in (self.user_environ, self.view_environ):
            if hasattr(x, name):
                return getattr(x, name)
        raise AttributeError(name)
    
    def _setup_router(self):
        self.router = ReRouter()


def test_main():
    model_environ = ModelContext('sqlite://')
    user_environ = UserContext('main-', model_environ)
    view_environ = ViewContext()
    user_controller = UserController(user_environ, view_environ)

if __name__ == '__main__':
    from ..test import run
    run()
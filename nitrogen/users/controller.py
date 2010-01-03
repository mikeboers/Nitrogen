

from nitrogen.route.rerouter import ReRouter
from .environ import UserEnviron
from ..model.environ import ModelEnviron
from ..view.environ import ViewEnviron

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
    model_environ = ModelEnviron('sqlite://')
    user_environ = UserEnviron('main-', model_environ)
    view_environ = ViewEnviron()
    user_controller = UserController(user_environ, view_environ)

if __name__ == '__main__':
    from ..test import run
    run()
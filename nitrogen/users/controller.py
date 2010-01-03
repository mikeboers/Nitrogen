
from ..request import as_request
from ..model.context import ModelContext
from ..route.rerouter import ReRouter
from ..view.context import ViewContext
from .context import UserContext



class UserController(object):
    
    def __init__(self, user_context, view_context):
        self.user_context = user_context
        self.view_context = view_context
        self._setup_router()
    
    def __getattr__(self, name):
        for x in (self.user_context, self.view_context):
            if hasattr(x, name):
                return getattr(x, name)
        raise AttributeError(name)
    
    def _setup_router(self):
        self.router = ReRouter()
        self.router.register('', self.do_index)
    
    @as_request
    def do_index(self, req, res):
        res.start()
        yield 'user index'


def test_main():
    model_context = ModelContext('sqlite://')
    user_context = UserContext('main-', model_context)
    view_context = ViewContext()
    user_controller = UserController(user_context, view_context)

if __name__ == '__main__':
    from ..test import run
    run()

from ..model.context import ModelContext
from ..request import as_request
from ..route.rerouter import ReRouter
from ..view.context import ViewContext
from .anon import AnonymousUser
from .context import UserContext



class UserController(object):
    
    def __init__(self, user_context, view_context, environ_key='user'):
        self.user_context = user_context
        self.view_context = view_context
        self.environ_key = environ_key
        self._setup_router()
    
    def __getattr__(self, name):
        for x in (self.user_context, self.view_context):
            if hasattr(x, name):
                return getattr(x, name)
        raise AttributeError(name)
    
    def _setup_router(self):
        self.router = ReRouter()
        self.router.register('/', self.do_index)
        self.router.register('/login', self.do_login)
    
    def restore_user(self, app):
        """WSGI middleware to put the user back into the environ."""
        def UserController_restore_user_inner(environ, start):
            cookies = environ.get('nitrogen.cookies')
            environ[self.environ_key] = AnonymousUser()
            return app(environ, start)
        return UserController_restore_user_inner
    
    def __call__(self, *args):
        return self.router(*args)
    
    @as_request
    def do_index(self, req, res):
        res.start()
        yield 'user index'
    
    @as_request
    def do_login(self, req, res):
        res.start()
        yield self.render('login.tpl')


def test_main():
    model_context = ModelContext('sqlite://')
    user_context = UserContext('main-', model_context)
    view_context = ViewContext()
    user_controller = UserController(user_context, view_context)

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

from beaker.middleware import SessionMiddleware

from . import app


class SessionAppMixin(app.Core):
    
    def setup(self):
        
        super(SessionAppMixin, self).setup()
        app = self.wrapped_wsgi_app
        
        opts = {}
        for key in self.config:
            if key.startswith('session_'):
                opts[key[8:]] = self.config[key]
        
        if not opts:
            opts = dict(
                type='ext:database',
                url='sqlite://',
                key='session_id',
                secret=os.urandom(32),
            )
        
        opts['key'] = opts.get('key', 'session_id')
        opts['secret'] = self.config.get('private_key', 'set this!')
        app = SessionMiddleware(app, **opts)
        
        self.wrapped_wsgi_app = app
        
        
        
        
        
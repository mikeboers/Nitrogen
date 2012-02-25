import os

from nitrogen.core import *

root = os.path.dirname(os.path.abspath(__file__))

app = App(
    debug=True,
    db_bind='sqlite://',
    private_key=os.urandom(128),
    
    template_path=[root + '/templates'],
    template_cache_dir=root + '/templates',

    session_type='ext:database',
    session_url='sqlite:///' + root + '/sessions.sqlite',
    session_lock_dir='/tmp/' + __name__,
    
    recaptcha_private_key='6LdCprwSAAAAALD_xUJfPSp0uG-prJFLydoZJ-Ro',
    recaptcha_public_key='6LdCprwSAAAAALonrXY3m6LtMEEVh4ZVZi0pZ04n',
    

)

# Dump all app exports into the global namespace.
app.export_to(globals())

# Register our controllers.
app.router.register_module('/', __package__) # Index.
app.router.register_package(None, __package__ + '.controllers', recursive=True)

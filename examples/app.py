import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *
from nitrogen.files import StaticRouter

root = os.path.dirname(os.path.abspath(__file__))

app = App(
    db_bind='sqlite://',
    private_key=os.urandom(128),
    session_type='ext:database',
    session_url='sqlite:///' + root + '/sessions.sqlite',
    session_lock_dir='/tmp/' + __name__,
    debug=True,
    recaptcha_private_key='6LdCprwSAAAAALD_xUJfPSp0uG-prJFLydoZJ-Ro',
    recaptcha_public_key='6LdCprwSAAAAALonrXY3m6LtMEEVh4ZVZi0pZ04n',
    template_path=[root + '/templates']
)

app.export_to(globals())
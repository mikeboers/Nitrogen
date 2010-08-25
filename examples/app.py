import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *

app = App(
    db_bind='sqlite://',
    private_key=os.urandom(128),
    private_key_material=os.urandom(128),
    session_type='ext:database',
    session_url='sqlite:///' + os.path.abspath(os.path.dirname(__file__) + '/sessions.sqlite'),
    session_lock_dir='/tmp/' + __name__,
    debug=True,
)

app.export_to(globals())
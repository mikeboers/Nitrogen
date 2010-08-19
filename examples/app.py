import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *

app = App(
    db_bind='sqlite://',
    private_key=os.urandom(128),
)

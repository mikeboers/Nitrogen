import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *

app = App(
    db_bind='sqlite://',
    private_key=os.urandom(128),
)

app.setup()

Request = app.request_class
Response = app.response_class
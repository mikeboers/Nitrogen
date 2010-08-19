
from nitrogen.wsgi.server import serve
from nitrogen.core import *

app = App()

@app.route('/')
def index(environ, start):
    start('200 OK', [])
    return ['Hello, world!']

serve('socket', app)

import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *

from .app import app
from .cookies import cookie_app

app.route('/cookies', cookie_app)

@app.route('/')
def index(environ, start):
    start('200 OK', [])
    return ['Hello, world!']

@app.route('/env')
def env(environ, start):
    start('200 OK', [])
    for x in sorted(environ.items()):
        yield '%s: %r\n' % x

@app.route('/request')
def request(environ, start):
    
    req = app.request
    start('200 ok', [])

    yield "This is %s req!\n\n" % req.method

    yield 'ENVIRON:\n'
    for k, v in sorted(req.environ.items()):
        if k in ('nitrogen.headers', 'HTTP_IF_NONE_MATCH'):
            v = '-'
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "HEADERS:\n"
    for k, v in sorted(req.headers.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "COOKIES:\n"
    for k, v in sorted(req.cookies.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "GET:\n"
    for k, v in sorted(req.get.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "EXTRA:\n"
    yield '\tuser_agent: %r\n' % req.user_agent
    yield '\t\tplatform: %r\n' % req.user_agent.platform
    yield '\t\tbrowser: %r\n' % req.user_agent.browser
    yield '\t\tversion: %r\n' % req.user_agent.version
    yield '\taccept: %r\n' % req.accept
    yield '\taccept_charset: %r\n' % req.accept_charset
    yield '\taccept_encoding: %r\n' % req.accept_encoding
    yield '\taccept_language: %r\n' % req.accept_language
    yield '\tcache_control: %r\n' % req.cache_control
    yield '\t\tmax_age: %r\n' % (req.cache_control and req.cache_control.max_age)
    yield '\tif_modified_since: %r\n' % req.if_modified_since
    yield '\n'

    yield 'DONE'



if __name__ == '__main__':
    app.run('socket')


import os

from nitrogen.wsgi.server import serve
from nitrogen.core import *
from nitrogen.status import abort

from .app import app, Request, Response
from .cookies import cookie_app
from .response import response_app

app.route('/cookies', cookie_app)
app.route('/response', response_app)

@app.route('/abort', code=400)
@app.route('/abort/{code:\d+}', _parsers=dict(code=int))
@Request.application
def do_abort(request):
    abort(request.route['code'])

@app.route('/exception', message='Testing')
@app.route('/exception/{message:.+}')
@Request.application
def do_abort(request):
    raise ValueError(request.route['message'])


@app.route('/')
def index(environ, start):
    start('200 OK', [])
    return ['Hello, world!']

@app.route('/env')
def env(environ, start):
    start('200 OK', [])
    for x in sorted(environ.items()):
        yield '%s: %r\n' % x

@app.route('/session')
@Request.application
def do_session(request):
    count = request.session.get('counter', 0) + 1
    request.session['counter'] = count
    request.session.save()
    return Response('Counter: %d' % count)


@app.route('/flash-show')
def do_flash_show(environ, start):
    msgs = app.get_flash_messages()
    
    Response(start=start).start()
    
    yield '%d flash message(s)\n' % len(msgs)
    for cls, message in msgs:
        yield '%s: %r\n' % (cls, message)


@app.route('/flash', message='Default message.')
@app.route('/flash/{message:.+}')
def do_flash(environ, start):
    app.flash(Request(environ).route['message'])    
    Response().redirect('/flash-show', start=start)
    return []


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
    yield '\taccept:\n'
    yield '\t\tcharsets: %r\n' % req.accept_charsets
    yield '\t\tencodings: %r\n' % req.accept_encodings
    yield '\t\tlanguages: %r\n' % req.accept_languages
    yield '\t\tmimetypes: %r\n' % req.accept_mimetypes
    yield '\tauthorization: %r\n' % req.authorization
    yield '\tcache_control: %r\n' % req.cache_control
    yield '\t\tmax_age: %r\n' % req.cache_control.max_age
    yield '\tif_match: %r\n' % req.if_match
    yield '\tif_modified_since: %r\n' % req.if_modified_since
    yield '\tif_none_match: %r\n' % req.if_none_match
    yield '\tuser_agent: %r\n' % req.user_agent
    yield '\t\tplatform: %r\n' % req.user_agent.platform
    yield '\t\tbrowser: %r\n' % req.user_agent.browser
    yield '\t\tversion: %r\n' % req.user_agent.version
    yield '\n'

    yield 'DONE'



if __name__ == '__main__':
    app.run('socket')

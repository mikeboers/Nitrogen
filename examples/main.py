
import os
import logging
import time

from nitrogen.core import *
from nitrogen.status import abort
from nitrogen.api import ApiRequest as Api
from nitrogen.forms import *

from .app import *
from .cookies import cookie_app
from .response import response_app
from .script import script_app
from .crud import crud_app

log = logging.getLogger(__name__)


app.route('/cookies', cookie_app)
app.route('/response', response_app)
app.route('/script', script_app)
app.route('/crud', crud_app)

@app.route('/stream')
def do_stream(environ, start):
    start('200 OK', [])
    for i in range(50):
        yield '%d ' % i
        time.sleep(0.1)
    

@app.route('/captcha')
@Request.application
def do_captcha(request):
    
    class CaptchaForm(Form):
        
        name = TextField(validators=[validators.Required()])
        captcha = RecaptchaField('Verify you are human')
    
    if request.is_post:
        form = CaptchaForm(request.form)
        valid = form.validate()
        log.debug('valid: %r' % valid)
    else:
        form = CaptchaForm()
        
    html = '<form method="POST">%s<br /><input type="submit"></form>' % form.render()
    return Response(html, mimetype='text/html')
    
    
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

@app.route('/api/reflect')
@Api.application
def do_api_reflect(request):
    response = dict(request.query)
    response.update(request.post)
    return response

@app.route('/api/error')
@Api.application
def do_api_error(request):
    request['id']
    request.abort(400, 'This is the message.')
    
@app.route('/')
@Request.application
def index(request):
    return Response('Hello, world!')

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
    app.flash(request.route['message'])    
    Response().redirect('/flash-show', start=start)
    return []


@app.route('/request')
def do_request(environ, start):
    
    # Get these cached into the environ.
    # request = Request(environ)
    request.query
    
    start('200 ok', [])

    yield "This is %s request!\n\n" % request.method

    yield 'ENVIRON:\n'
    for k, v in sorted(request.environ.items()):
        if k in ('nitrogen.headers', 'HTTP_IF_NONE_MATCH'):
            v = '-'
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "HEADERS:\n"
    for k, v in sorted(request.headers.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "COOKIES:\n"
    for k, v in sorted(request.cookies.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "QUERY:\n"
    for k, v in sorted(request.query.items()):
        yield "\t%s: %r\n" % (k, v)
    yield '\n'

    yield "PARSED HEADERS:\n"
    yield '\taccept:\n'
    yield '\t\tcharsets: %r\n' % request.accept_charsets
    yield '\t\tencodings: %r\n' % request.accept_encodings
    yield '\t\tlanguages: %r\n' % request.accept_languages
    yield '\t\tmimetypes: %r\n' % request.accept_mimetypes
    yield '\tauthorization: %r\n' % request.authorization
    yield '\tcache_control: %r\n' % request.cache_control
    yield '\t\tmax_age: %r\n' % request.cache_control.max_age
    yield '\tif_match: %r\n' % request.if_match
    yield '\tif_modified_since: %r\n' % request.if_modified_since
    yield '\tif_none_match: %r\n' % request.if_none_match
    yield '\tuser_agent: %r\n' % request.user_agent
    yield '\t\tplatform: %r\n' % request.user_agent.platform
    yield '\t\tbrowser: %r\n' % request.user_agent.browser
    yield '\t\tversion: %r\n' % request.user_agent.version
    yield '\n'
    
    yield 'Extra\n'
    for name in sorted('''
        host
        host_url
        is_behind_proxy
        is_multiprocess
        is_multithread
        is_run_once
        is_secure
        is_xhr
        method
        path
        query_string
        remote_addr
        remote_user
        script_root
        url
        url_root
        referrer
        date
        script_name
        path_info
    '''.strip().split()):
        yield '\t%s: %r\n' % (name, getattr(request, name))
    yield '\n'
    
    yield 'DONE'

if __name__ == '__main__':
    from nitrogen.serve import serve_via_socket as serve
    serve(app)

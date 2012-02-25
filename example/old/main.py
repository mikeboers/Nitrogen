
import os
import logging
import time

from nitrogen.core import *
from nitrogen.forms import *
from nitrogen import status

from .app import *


log = logging.getLogger(__name__)





    

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


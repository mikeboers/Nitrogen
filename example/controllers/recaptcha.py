from nitrogen import forms
from . import *

@route('/')
def do_captcha(request):
    
    class CaptchaForm(app.Form):
        
        name = forms.TextField(validators=[forms.validators.Required()])
        captcha = app.RecaptchaField('Verify you are human')
    
    if request.method == 'POST':
        form = CaptchaForm(request.form)
        valid = form.validate()
        log.debug('valid: %r' % valid)
    else:
        form = CaptchaForm()
        
    html = 'THIS EXAMPLE IS KNOWN TO NOT WORK!<br /><form method="POST">%s<br /><input type="submit"></form>' % form.render()
    return Response(html, mimetype='text/html')

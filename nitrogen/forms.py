
import werkzeug as wz

from wtforms import *
from wtforms.ext.sqlalchemy.orm import model_form
import wtforms

from nitrogen.recaptcha import RecaptchaField

from . import app



class MarkdownField(TextAreaField):
    pass


class FormAppMixin(object):
    
    class FormMixin(object):
        def render(self):
            return self._app.render('/form.html', form=self)
    
    build_form_class = lambda self: app.build_inheritance_mixin_class(self.__class__, Form, 'Form')
    Form = wz.cached_property(build_form_class, name='Form')
        
    def __init__(self, *args, **kwargs):
        FormAppMixin.FormMixin._app = self
        super(FormAppMixin, self).__init__(*args, **kwargs)
        
        RecaptchaField.remote_addr = lambda *args: self.request.remote_addr
        
        # Monkey patch!
        #recaptcha_validators.request = self.request
        #recaptcha_validators.current_app = self
        #recaptcha_widgets.current_app = self
        
    def export_to(self, map):
        super(FormAppMixin, self).export_to(map)
        map['Form'] = self.Form
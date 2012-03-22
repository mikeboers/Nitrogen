from __future__ import absolute_import

import sys

import wtforms

from .. import mixin
from .. import recaptcha

__all__ = ['FormAppMixin']


class FormAppMixin(object):
    
    class FormMixin(object):
        def render(self):
            return self._app.render('/_wtform.html', form=self)
    
    Form = mixin.builder_property(wtforms.Form)
    
    def __init__(self, *args, **kwargs):
        FormAppMixin.FormMixin._app = self
        super(FormAppMixin, self).__init__(*args, **kwargs)
        
        self.RecaptchaField = type('RecaptchaField', (recaptcha.RecaptchaField, ), {
            'remote_addr': lambda *args: self.request.remote_addr,
            'public_key': self.config.recaptcha_public_key,
            'private_key': self.config.recaptcha_private_key,
            'use_ssl': self.config.recaptcha_use_ssl,
            'options': self.config.recaptcha_options,
        })
    
    def setup_config(self):
        super(FormAppMixin, self).setup_config()
        self.config.setdefault('recaptcha_use_ssl', True)
        
    def export_to(self, map):
        super(FormAppMixin, self).export_to(map)
        map['Form'] = self.Form
        map['RecaptchaField'] = self.RecaptchaField

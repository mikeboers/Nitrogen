
from wtforms import *
from wtforms.ext.sqlalchemy.orm import model_form
import wtforms


__all__ = dir()


from . import app


__all__.extend(['MarkdownField'])


class MarkdownField(TextAreaField):
    pass


class FormAppMixin(object):
    
    _build_form_class = app.class_builder(Form, 'Form')
    def build_form_class(self):
        cls = self._build_form_class()
        cls._app = self
        return cls
    
    class FormMixin(object):
        def render(self):
            return self._app.render('/form.html', form=self)
        
    def __init__(self, *args, **kwargs):
        super(FormAppMixin, self).__init__(*args, **kwargs)
        self.Form = self.build_form_class()
    
    def export_to(self, map):
        super(FormAppMixin, self).export_to(map)
        map['Form'] = self.Form
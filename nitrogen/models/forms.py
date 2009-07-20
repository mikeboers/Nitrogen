# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen.models'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import datetime
import formalchemy
import logging

class DateTimeRenderer(formalchemy.fields.FieldRenderer):
    """Date input that relies on the editable plugin to manage the input with
    date.js
    
    The page must return a "YYYY-MM-DD HH-MM-SS" like string for the default
    validator to deal with it.
    """
    def render(self, **kwargs):
        if isinstance(self._value, datetime.datetime):
            value = self._value.strftime("%A, %B %d, %Y %I:%M:%S %p")
        else:
            value = self._value
        return formalchemy.helpers.text_field(self.name, value=value, class_="datetime", **kwargs)


class MarkdownRenderer(formalchemy.fields.FieldRenderer):
    """Markdown textarea.
    
    Only sends down a "markdown" class which the editable plugin knows to set
    up as a markdown editor.
    """
    def render(self, **kwargs):
        return formalchemy.helpers.text_area(self.name, content=self._value, class_="markdown", **kwargs)

class FieldSet(formalchemy.FieldSet):
    
    def __init__(self, *args, **kwargs):
        formalchemy.FieldSet.__init__(self, *args, **kwargs)
        self._render = None
        self._render_readonly = None
    
    def render(self, **kwargs):
        from ..views import render
        logging.debug('FieldSet.render(**%r)' % kwargs)
        return render('_formalchemy.tpl', fieldset=self, **kwargs)


FieldSet.default_renderers[formalchemy.types.DateTime] = DateTimeRenderer

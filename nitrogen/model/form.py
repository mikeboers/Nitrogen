"""Extending a couple formalchemy renderers."""

# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = '.'.join(name[:-3].split(os.path.sep)[:-1])
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)


import datetime

import formalchemy


class TextFieldRenderer(formalchemy.fields.TextFieldRenderer):
    def render(self, **kwargs):
        return formalchemy.helpers.text_field(self.name, class_='text', value=self._value, maxlength=self.length, **kwargs)


class FloatFieldRenderer(formalchemy.fields.FloatFieldRenderer):
    def render(self, **kwargs):
        return formalchemy.helpers.text_field(self.name, class_='text', value=self._value, **kwargs)


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
        return formalchemy.helpers.text_field(self.name, value=value, class_="text datetime", **kwargs)


class MarkdownRenderer(formalchemy.fields.FieldRenderer):
    """Markdown textarea.
    
    Only sends down a "markdown" class which the editable plugin knows to set
    up as a markdown editor.
    """
    def render(self, **kwargs):
        return formalchemy.helpers.text_area(self.name, content=self._value, class_="markdown", **kwargs)


def build_form_class(render):
    class Form(formalchemy.FieldSet):
        def _render(self, fieldset, **kwargs):
            return render('_formalchemy.tpl', fieldset=fieldset, **kwargs)

    Form.default_renderers[formalchemy.types.DateTime] = DateTimeRenderer
    Form.default_renderers[formalchemy.types.String] = TextFieldRenderer
    Form.default_renderers[formalchemy.types.Float] = FloatFieldRenderer
    Form.default_renderers[formalchemy.types.Numeric] = FloatFieldRenderer
    
    return Form

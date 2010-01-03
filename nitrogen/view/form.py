"""Extending a couple formalchemy renderers."""


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


def build_fieldset_class(render):
    class FieldSet(formalchemy.FieldSet):
        def _render(self, fieldset, **kwargs):
            return render('_formalchemy.tpl', fieldset=fieldset, **kwargs)

    FieldSet.default_renderers[formalchemy.types.DateTime] = DateTimeRenderer
    FieldSet.default_renderers[formalchemy.types.String] = TextFieldRenderer
    FieldSet.default_renderers[formalchemy.types.Float] = FloatFieldRenderer
    FieldSet.default_renderers[formalchemy.types.Numeric] = FloatFieldRenderer
    
    return FieldSet

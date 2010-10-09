# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285969458.772135
_template_filename='/srv/secrettrial5.com/src/nitrogen/templates/form.html'
_template_uri='/form.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = []


def render_body(context,form,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs,form=form)
        json = context.get('json', UNDEFINED)
        error = context.get('error', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2

        import os
        nonce = os.urandom(4).encode('hex')
        form_id = 'form-%s' % nonce
        
        
        __M_locals_builtin_stored = __M_locals_builtin()
        __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin_stored[__M_key]) for __M_key in ['nonce','os','form_id'] if __M_key in __M_locals_builtin_stored]))
        # SOURCE LINE 6
        __M_writer(u'\n<ol id="')
        # SOURCE LINE 7
        __M_writer(unicode(form_id))
        __M_writer(u'" class="form-fields">\n')
        # SOURCE LINE 8
        for field in form:
            # SOURCE LINE 9
            __M_writer(u'    <li class="state-')
            __M_writer(unicode("error" if field.errors else "ok"))
            __M_writer(u'">\n      <div class="label">\n')
            # SOURCE LINE 11
            if field.type == 'BooleanField':
                # SOURCE LINE 12
                __M_writer(u'            ')
                __M_writer(unicode(field()))
                __M_writer(u'\n')
                pass
            # SOURCE LINE 14
            __M_writer(u'        ')
            __M_writer(unicode(field.label()))
            __M_writer(u'\n')
            # SOURCE LINE 15
            if field.flags.optional:
                # SOURCE LINE 16
                __M_writer(u'          <span class="optional">(optional)</span>\n')
                # SOURCE LINE 17
            elif field.flags.required:
                # SOURCE LINE 18
                __M_writer(u'          <span class="required">(required)</span>\n')
                pass
            # SOURCE LINE 20
            if field.errors:
                # SOURCE LINE 21
                __M_writer(u'          <ol class="errors">\n            ')
                # SOURCE LINE 22
                __M_writer(unicode('\n'.join('<li>[ %s ]</li>' % error for error in field.errors)))
                __M_writer(u'\n          </ol>\n')
                pass
            # SOURCE LINE 25
            __M_writer(u'      </div>\n')
            # SOURCE LINE 26
            if field.type != 'BooleanField':
                # SOURCE LINE 27
                __M_writer(u'      <div class="field type-')
                __M_writer(unicode(field.type))
                __M_writer(u'">\n        ')
                # SOURCE LINE 28
                __M_writer(unicode(field()))
                __M_writer(u'\n      </div>\n')
                pass
            # SOURCE LINE 31
            if field.type == 'MarkdownField':
                # SOURCE LINE 32
                __M_writer(u'        <script>jQuery(function($) {\n          if ($.markdownEditor)\n            $(')
                # SOURCE LINE 34
                __M_writer(unicode(json('#%s #%s' % (form_id, field.name))))
                __M_writer(u').markdownEditor();\n        })</script>\n')
                # SOURCE LINE 36
            elif field.type in ('DateField', 'DateTimeField'):
                # SOURCE LINE 37
                __M_writer(u'        <script>jQuery(function($) {\n          if ($.autodate)\n            $(')
                # SOURCE LINE 39
                __M_writer(unicode(json('#%s #%s' % (form_id, field.name))))
                __M_writer(u').autodate({type:')
                __M_writer(json(unicode(field.type[:-5].lower())))
                __M_writer(u'});\n        })</script>\n')
                pass
            # SOURCE LINE 42
            __M_writer(u'    </li>\n')
            pass
        # SOURCE LINE 44
        __M_writer(u'</ol>')
        return ''
    finally:
        context.caller_stack._pop_frame()



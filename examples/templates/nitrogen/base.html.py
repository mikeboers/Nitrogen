# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285968335.459389
_template_filename=u'/srv/secrettrial5.com/src/nitrogen/templates/nitrogen/base.html'
_template_uri=u'/nitrogen/base.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = ['head', 'page_title', 'post_html']


# SOURCE LINE 1


page_title = ''



def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        capture = context.get('capture', UNDEFINED)
        self = context.get('self', UNDEFINED)
        next = context.get('next', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 5
        __M_writer(u'\n<html>\n\t<head>\n')
        # SOURCE LINE 8
        if self.attr.page_title:
            # SOURCE LINE 9
            __M_writer(u'\t\t\t<title>')
            __M_writer(filters.html_escape(unicode(self.attr.page_title)))
            __M_writer(u'</title>\n')
            # SOURCE LINE 10
        else:
            # SOURCE LINE 11
            __M_writer(u'\t\t\t')
            page_title = capture(self.page_title).strip() 
            
            __M_locals_builtin_stored = __M_locals_builtin()
            __M_locals.update(__M_dict_builtin([(__M_key, __M_locals_builtin_stored[__M_key]) for __M_key in ['page_title'] if __M_key in __M_locals_builtin_stored]))
            __M_writer(u'')
            # SOURCE LINE 12
            if page_title:
                # SOURCE LINE 13
                __M_writer(u'\t\t\t\t<title>')
                __M_writer(unicode(page_title))
                __M_writer(u'</title>\n')
                pass
            pass
        # SOURCE LINE 16
        __M_writer(u'\t\t')
        __M_writer(unicode(next.head()))
        __M_writer(u'\n\t</head>\n\t<body>\n\t\t')
        # SOURCE LINE 19
        __M_writer(unicode(next.body()))
        __M_writer(u'\n\t</body>\n</html>\n')
        # SOURCE LINE 22
        __M_writer(unicode(next.post_html()))
        __M_writer(u'\n')
        # SOURCE LINE 23
        __M_writer(u'\n')
        # SOURCE LINE 24
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_head(context):
    context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_page_title(context):
    context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_post_html(context):
    context.caller_stack._push_frame()
    try:
        __M_writer = context.writer()
        return ''
    finally:
        context.caller_stack._pop_frame()



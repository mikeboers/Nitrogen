# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285969026.7415681
_template_filename='/srv/secrettrial5.com/src/nitrogen/examples/templates/script/index.html'
_template_uri='/script/index.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = ['function']


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        self = context.get('self', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 3
        __M_writer(u'\n')
        def ccall(caller):
            def body():
                __M_writer = context.writer()
                return ''
            return [body]
        caller = context.caller_stack._get_caller()
        context.caller_stack.nextcaller = runtime.Namespace('caller', context, callables=ccall(caller))
        try:
            # SOURCE LINE 4
            __M_writer(unicode(self.function(a=u'1',b=u'2')))
        finally:
            context.caller_stack.nextcaller = None
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_function(context,**kwargs):
    context.caller_stack._push_frame()
    try:
        repr = context.get('repr', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n    Called with ')
        # SOURCE LINE 2
        __M_writer(filters.html_escape(unicode(repr(kwargs))))
        __M_writer(u'\n')
        return ''
    finally:
        context.caller_stack._pop_frame()



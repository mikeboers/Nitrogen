# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285968335.4448459
_template_filename='/srv/secrettrial5.com/src/nitrogen/templates/status/generic.html'
_template_uri='/status/generic.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = ['page_title', 'post_html']


def _mako_get_namespace(context, name):
    try:
        return context.namespaces[(__name__, name)]
    except KeyError:
        _mako_generate_namespaces(context)
        return context.namespaces[(__name__, name)]
def _mako_generate_namespaces(context):
    pass
def _mako_inherit(template, context):
    _mako_generate_namespaces(context)
    return runtime._inherit_from(context, u'/nitrogen/base.html', _template_uri)
def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        environ = context.get('environ', UNDEFINED)
        exception = context.get('exception', UNDEFINED)
        def page_title():
            return render_page_title(context.locals_(__M_locals))
        html_report = context.get('html_report', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n')
        # SOURCE LINE 2
        __M_writer(u'\n\n<h1>')
        # SOURCE LINE 4
        __M_writer(unicode(page_title()))
        __M_writer(u'</h1>\n<p>')
        # SOURCE LINE 5
        __M_writer(filters.html_escape(unicode(exception.explanation)))
        __M_writer(u'</p>\n')
        # SOURCE LINE 6
        if exception.detail:
            # SOURCE LINE 7
            __M_writer(u'\t<p><em>')
            __M_writer(filters.html_escape(unicode(exception.detail)))
            __M_writer(u'</em></p>\n')
            pass
        # SOURCE LINE 9
        if exception.comment:
            # SOURCE LINE 10
            __M_writer(u'\t<!-- ')
            __M_writer(unicode(exception.comment))
            __M_writer(u' -->\n')
            pass
        # SOURCE LINE 12
        __M_writer(u'<hr noshade>\n')
        # SOURCE LINE 13
        if html_report:
            # SOURCE LINE 14
            __M_writer(u'\t')
            __M_writer(unicode(html_report))
            __M_writer(u'\n\t<hr noshade>\n')
            pass
        # SOURCE LINE 17
        __M_writer(u'<div align="right">')
        __M_writer(filters.html_escape(unicode(environ['SERVER_NAME'])))
        __M_writer(u'</div>\n\n')
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_page_title(context):
    context.caller_stack._push_frame()
    try:
        exception = context.get('exception', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 2
        __M_writer(unicode(exception.code))
        __M_writer(u': ')
        __M_writer(filters.html_escape(unicode(exception.title)))
        return ''
    finally:
        context.caller_stack._pop_frame()


def render_post_html(context):
    context.caller_stack._push_frame()
    try:
        text_report = context.get('text_report', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 19
        __M_writer(u'\n')
        # SOURCE LINE 20
        if text_report:
            # SOURCE LINE 21
            __M_writer(u'<!--\n')
            # SOURCE LINE 22
            __M_writer(unicode(text_report))
            __M_writer(u'\n-->\n')
            pass
        return ''
    finally:
        context.caller_stack._pop_frame()



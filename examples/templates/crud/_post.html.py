# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285969455.0201631
_template_filename=u'/srv/secrettrial5.com/src/nitrogen/examples/templates/crud/_post.html'
_template_uri=u'/crud/_post.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = []


def render_body(context,post,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(post=post,pageargs=pageargs)
        markdown = context.get('markdown', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'\n<div id="post-')
        # SOURCE LINE 2
        __M_writer(unicode(post.id))
        __M_writer(u'" class="post">\n    <h2>')
        # SOURCE LINE 3
        __M_writer(filters.html_escape(unicode(post.title)))
        __M_writer(u'</h2>\n    <h3>')
        # SOURCE LINE 4
        __M_writer(filters.html_escape(unicode(post.post_time)))
        __M_writer(u'</h3>\n    <p>')
        # SOURCE LINE 5
        __M_writer(markdown(unicode(post.body)))
        __M_writer(u'</p>\n</div>')
        return ''
    finally:
        context.caller_stack._pop_frame()



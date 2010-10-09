# -*- encoding:utf-8 -*-
from mako import runtime, filters, cache
UNDEFINED = runtime.UNDEFINED
__M_dict_builtin = dict
__M_locals_builtin = locals
_magic_number = 5
_modified_time = 1285969454.9970551
_template_filename='/srv/secrettrial5.com/src/nitrogen/examples/templates/crud/index.html'
_template_uri='/crud/index.html'
_template_cache=cache.Cache(__name__, _modified_time)
_source_encoding='utf-8'
_exports = []


def render_body(context,**pageargs):
    context.caller_stack._push_frame()
    try:
        __M_locals = __M_dict_builtin(pageargs=pageargs)
        posts = context.get('posts', UNDEFINED)
        __M_writer = context.writer()
        # SOURCE LINE 1
        __M_writer(u'<html>\n<head>\n    \n    <script src="/js/jquery-1.4.2.min.js"></script>\n    <script src="/js/jquery-ui-1.8.5.min.js"></script>\n    <script src="/js/jquery.crud.js"></script>\n    <script src="/js/jquery.blockUI.js"></script>\n    <script src="/js/date.js"></script>\n    <script src="/js/jquery.autodate.js"></script>\n    <script src="/js/jquery.markdownEditor.js"></script>\n    <script src="/js/jquery.textarearesizer.js"></script>\n    <script src="/js/jquery.selection.js"></script>\n    \n    <link rel="stylesheet" href="/css/smoothness/jquery-ui-1.8.5.css">\n    <link rel="stylesheet" href="/css/framework/screen.css">\n    <link rel="stylesheet" href="/css/silk.css">\n    <style>\n        .post {\n            margin: 10px;\n            padding: 10px;\n            width: 50%;\n        }\n        .post.crud-active {\n            padding: 0;\n        }\n    </style>\n</head>\n<body>\n\n<h1>Posts:</h1>\n')
        # SOURCE LINE 31
        for post in posts:
            # SOURCE LINE 32
            __M_writer(u'    ')
            runtime._include_file(context, u'_post.html', _template_uri, post=post)
            __M_writer(u"\n    <script>jQuery(function($){\n        $('#post-")
            # SOURCE LINE 34
            __M_writer(unicode(post.id))
            __M_writer(u"').crud({url:'/crud/api', id:")
            __M_writer(unicode(post.id))
            __M_writer(u'})\n    })</script>\n')
            pass
        return ''
    finally:
        context.caller_stack._pop_frame()



"""Module for WSGI status helping functions."""

from __future__ import absolute_import

import sys
import re
import logging
from httplib import responses as _code_to_message

from paste import httpexceptions as _httpexceptions
from paste.util.quoting import strip_html, html_quote, no_quote, comment_quote

log = logging.getLogger(__name__)


_message_to_code = dict((v.lower(), k) for k, v in _code_to_message.items())


exceptions = {}


class _Mixin(object):
    
    # I am intensionally leaving the closing tags off here so that extra can
    # be appended by whatever is calling the exception.
    html_template = (
    '<html>\r'
    '  <head><title>%(title)s</title></head>\r'
    '  <body>\r'
    '    <h1>%(title)s</h1>\r'
    '    <p>%(body)s</p>\r'
    '    <hr noshade>\r'
    '    <div align="right">%(server)s</div>\r'
    )
    
    def html(self, environ):
        """ text/html representation of the exception """
        body = self.make_body(environ, self.template, html_quote, comment_quote)
        return self.html_template % {
                   'title': self.title,
                   'code': self.code,
                   'server': environ['SERVER_NAME'],
                   'body': body }
    
    # A few things to make them look more like Werkzeug Responses.
    @property
    def status_code(self):
        return self.code
    
    def get_response(self, environ):
        from .request import Response
        headers, content = self.prepare_content(environ)
        return Response(content, self.code, headers)

                   

# Retrieve all of the exceptions, and set them to both the HTTP prefixed, and
# non-prefixed versions.
StatusException = HTTPException = _httpexceptions.HTTPException
Redirection = HTTPRedirection = _httpexceptions.HTTPRedirection
Move = HTTPMove = _httpexceptions._HTTPMove
Error = HTTPError = _httpexceptions.HTTPError
BadRequest = HTTPBadRequest = _httpexceptions.HTTPBadRequest
for name in dir(_httpexceptions):
    if not name.startswith('HTTP'):
        continue
    base = getattr(_httpexceptions, name)
    if not getattr(base, 'code', None):
        continue
    name = name[4:]
    cls = type(name, (_Mixin, base), {})
    globals()[name] = cls
    globals()['HTTP' + name] = cls
    exceptions[cls.code] = cls


def abort(code, *args, **kwargs):
    raise exceptions[code](*args, **kwargs)
    

def redirect(location, code=303, *args, **kwargs):
    raise exceptions[code](location, *args, **kwargs)





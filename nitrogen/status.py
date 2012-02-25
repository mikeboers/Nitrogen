"""Module for WSGI status helping functions."""

import logging

from werkzeug.exceptions import HTTPException, default_exceptions as _wz_exceptions
from werkzeug.utils import redirect


__all__ = ['HTTPException']


log = logging.getLogger(__name__)


# Pull in all the exceptions from Werkzeug.
for e in _wz_exceptions.itervalues():
    globals()[e.__name__] = e
del e

# Add a status_code synonym to make it look more like a Response
def _HTTPException_status_code(self):
    return self.code
HTTPException.status_code = property(_HTTPException_status_code)

# Backwards compatibility with Paste exceptions.
HTTPException.title = HTTPException.name
def _make_bc_property(name):
    @property
    def _bc_property(self):
        log.warning('something asked for Paste-style HTTPException.%s' % name)
        return ''
    return _bc_property
HTTPException.explanation = _make_bc_property('explanation')
HTTPException.detail = _make_bc_property('detail')    
HTTPException.comment = _make_bc_property('comment')



class HTTPRedirection(HTTPException):
    """Base class for 300's status code (redirections)."""
    pass

    def __init__(self, location, headers=None):
        super(HTTPRedirection, self).__init__(location)
        self.location = location
        self.headers = headers or []

    def get_response(self, environ):
        response = redirect(self.location, self.code)
        response.headers.extend(self.headers)
        return response
    
        
# All the other exceptions that Paste provides.  
class MultipleChoices(HTTPRedirection):
    code = 300
    title = 'Multiple Choices'

class MovedPermanently(HTTPRedirection):
    code = 301
    title = 'Moved Permanently'

class Found(HTTPRedirection):
    code = 302
    title = 'Found'

class SeeOther(HTTPRedirection):
    code = 303
    title = 'See Other'

class NotModified(HTTPException):
    code = 304
    title = 'Not Modified'
    message = ''
    def plain(self, environ):
        return ''
    def html(self, environ):
        return ''

class UseProxy(HTTPException):
    code = 305
    description = (
        '<p>The resource must be accessed through a proxy '
        'located at</p>')

class TemporaryRedirect(HTTPRedirection):
    code = 307


class PaymentRequired(HTTPException):
    code = 402
    description = ('<p>Access was denied for financial reasons.</p>')

NotFound.description = '<p>The requested URL was not found on the server.</p>'
Forbidden.description = "<p>You don't have the permission to access the requested resource.</p>"

class ProxyAuthenticationRequired(HTTPException):
    code = 407
    description = ('<p>Authentication /w a local proxy is needed.</p>')

class Conflict(HTTPException):
    code = 409
    description = ('<p>There was a conflict when trying to complete '
                   'your request.</p>')
                   
class RequestRangeNotSatisfiable(HTTPException):
   code = 416
   description = ('<p>The Range requested is not available.</p>')

class ExpectationFailed(HTTPException):
   code = 417
   description = ('<p>Expectation failed.</p>')


class GatewayTimeout(HTTPException):
   code = 504
   description = ('<p>The gateway has timed out.</p>')

class VersionNotSupported(HTTPException):
   code = 505
   description = ('<p>The HTTP version is not supported.</p>')
                                   

# Build up a dict, and set __all__.
exceptions = {}
for name, e in globals().items():
    if name.startswith('_'):
        continue
    if (
        isinstance(e, type) and
        issubclass(e, HTTPException) and
        isinstance(getattr(e, 'code', None), int)
    ):
        exceptions[e.code] = e
        __all__.append(name)


"""Module for WSGI status helping functions."""

from httplib import responses as _code_to_message

_message_to_code = dict((v.lower(), k) for k, v in _code_to_message.items())

def code_to_message(code):
    return _code_to_message[code]

def message_to_code(msg):
    return _message_to_code[' '.join(msg.strip().split()).lower()]

def normalize_message(msg):
    return code_to_message(message_to_code(msg))

def resolve_status(status):
    """Resolve a given object into the status that it should represent.
    
    Tries to anticipate what you are thinking. If you pass an int, it returns
    the proper message along with it. If you pass a message, it returns the
    proper int along with (the properly cased) message. None is returned as
    '200 OK'. Anthing else is returned unchanged.
    
    Note that we do NOT check to make sure statuses that are untouched are
    valid or not.
    
    Examples:
    
        >>> resolve_status(None)
        '200 OK'
        >>> resolve_status(200)
        '200 OK'
        >>> resolve_status("OK")
        '200 OK'
        >>> resolve_status('200 OK')
        '200 OK'
        
        >>> resolve_status(404)
        '404 Not Found'
        >>> resolve_status("not found")
        '404 Not Found'
        
        >>> resolve_status(401)
        '401 Unauthorized'
        >>> resolve_status('UNAUTHORIZED')
        '401 Unauthorized'
        
        >>> resolve_status('999 Not in List')
        '999 Not in List'
        >>> resolve_status('200 Custom Message')
        '200 Custom Message'
    
    """
    
    # None implies 200.
    if status is None:
        return '200 OK'
    
    # See if status is a status code.
    try:
        return '%d %s' % (status, code_to_message(status))
    except:
        pass
    
    # See if the constant is set
    try:
        return '%d %s' % (message_to_code(status), normalize_message(status))
    except:
        pass
    
    # Can't find it... just hand it back.
    return status


def status_resolver(app):
    """WSGI middleware which attempts to resolve whatever is sent as the
    status object into a proper HTTP status.
    
    """
    
    def inner(environ, start):
        def inner_start(status, headers):
            start(resolve_status(status), headers)
        return app(environ, inner_start)
    return inner


class BaseHttpStatus(Exception):
    _code = 200
    def __init__(self, *args):
        Exception.__init__(self, 'HTTP status code %d: %s' % (self._code, code_to_message(self._code)), *args)

def make_http_status_exception(code):
    message = code_to_message(code)
    name = 'Http' + ''.join(message.split())
    return type(name, (BaseHttpStatus, ), {'_code': code})


HttpOK = make_http_status_exception(200)

# All of the 300 class needs a Location header.
HttpMovedPermanently = make_http_status_exception(301)
HttpFound = make_http_status_exception(302)
HttpSeeOther = make_http_status_exception(303)
HttpNotModified = make_http_status_exception(304)
HttpTemporaryRedirect = make_http_status_exception(307)

HttpUnauthorized = make_http_status_exception(401) # This once needs a WWW-Authenticate header along with it.
HttpForbidden = make_http_status_exception(403)
HttpNotFound = make_http_status_exception(404)
HttpGone = make_http_status_exception(410)




def test_status_names():
    """Make sure that I didn't make a type when setting all of the generated
    HTTP status exception classes."""
    for name, obj in globals().items():
        try:
            check = issubclass(obj, BaseHttpStatus)
        except:
            pass
        else:
            if check:
                assert name == obj.__name__

def test_status_resolver():
    """Nose test, checking that plaintext is returned."""

    from webtest import TestApp
    
    @status_resolver
    def app(environ, start):
        start(307, [('Content-Type', 'text-plain')])
        yield 'Not found!'
    app = TestApp(app)

    res = app.get('/')
    assert res.status == '307 Temporary Redirect', 'Status did not get resolved.'

if __name__ == '__main__':
    from test import run
    run()
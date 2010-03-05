"""Module for WSGI status helping functions."""

from __future__ import absolute_import

import sys
import re

from httplib import responses as _code_to_message

_message_to_code = dict((v.lower(), k) for k, v in _code_to_message.items())


def code_to_message(code):
    """Convert a integer code into the canonical message.
    
    Examples:
        >>> code_to_message(200)
        'OK'
        >>> code_to_message(404)
        'Not Found'
    
    """
    try:
        return _code_to_message[int(code)]
    except KeyError:
        raise ValueError(code)


def message_to_code(msg):
    """Convert a status message into the coresponding integer code.
    
    Is case insenstive.
    
    Examples:
        >>> message_to_code('OK')
        200
        >>> message_to_code('ok')
        200
        >>> message_to_code('not found')
        404
    
    """
    try:
        return _message_to_code[str(msg).lower()]
    except KeyError:
        raise ValueError(msg)


def canonicalize_message(msg):
    """Return the canonical version of the HTTP status message.
    
    Raises ValueError if it can't do it.
    
    Examples:
        
        >>> canonicalize_message('not found')
        'Not Found'
        
    """
    return code_to_message(message_to_code(msg))


def resolve_status(status, canonicalize=False, strict=False):
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
        >>> resolve_status('999 Not in List', strict=True)
        Traceback (most recent call last):
        ...
        ValueError: can't resolve status '999 Not in List'
        >>> resolve_status('200 OK', strict=True)
        '200 OK'
        
        >>> resolve_status('200 Custom Message')
        '200 Custom Message'
        >>> resolve_status('200 Custom Message', canonicalize=True)
        '200 OK'
        
        >>> resolve_status('200')
        '200 OK'
        
    """
    
    # None implies 200.
    if status is None:
        return '200 OK'
    
    # Strings of numbers should be numbers
    try:
        status = int(status)
    except ValueError:
        if canonicalize:
            m = re.match(r'^(\d+)(\s|$)', str(status))
            if m:
                status = int(m.group(1))
    
    # Convert it to a code if we can.
    try:
        status = message_to_code(status)
    except ValueError:
        pass
    
    # See if status is a status code.
    try:
        return '%d %s' % (status, code_to_message(status))
    except ValueError:
        pass
    
    # Can't find it...
    if strict:
        code, msg = None, None
        m = re.match(r'^(\d+) (.+)$', status)
        if m:
            code, msg = m.groups()
        if not code or not msg or _code_to_message.get(int(code)) != msg:
            raise ValueError('can\'t resolve status %r' % status)
    return status


def status_resolver(app, canonicalize=False, strict=False):
    """WSGI middleware which attempts to resolve whatever is sent as the
    status object into a proper HTTP status.
    
    """
    
    def status_resolver_app(environ, start):
        def status_resolver_start(status, headers, exc_info=None):
            start(resolve_status(status, canonicalize=canonicalize, strict=strict), headers)
        return app(environ, status_resolver_start)
    return status_resolver_app


class BaseHttpStatus(Exception):
    """Base HTTP status exception from which all will inherit.
    
    This is not to be used directly.
    
    """
    _code = 200


_code_to_exception = {}
def exception(code):
    """Create a class for the given HTTP status code or message.
    
    Caches the Exception and also stores it as an attribute on this module.
    This is done so that they are easily Pickleable, and to make them easy to
    access by name from the outside.
    
    Example:
        >>> x = exception(400)
        >>> x.__name__, x._code
        ('HttpBadRequest', 400)
        
        >>> x = exception('See Other')
        >>> x.__name__, x._code
        ('HttpSeeOther', 303)
    
    """
    if not isinstance(code, int):
        code = message_to_code(code)
    if code not in _code_to_exception:
        message = code_to_message(code)
        name = 'Http' + ''.join(message.split())
        _code_to_exception[code] = obj = type(name, (BaseHttpStatus, ), {'_code': code})
        self = sys.modules[__name__]
        setattr(self, name    , obj) # Perhaps will depreciate this one?
        setattr(self, name[4:], obj)
    return _code_to_exception[code]


# Walk through all of the codes and make a class for each one, assigning it
# to this module (essentially putting it into the global namespace).
for code in _code_to_message:
    exception(code)



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
    import nose; nose.run(defaultTest=__name__)
"""Module for WSGI status helping functions."""

import httplib

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
    if status in httplib.responses:
        return '%d %s' % (status, httplib.responses[status])
    
    # See if the constant is set
    status_no = getattr(httplib, str(status).replace(' ', '_').upper(), None)
    if status_no is not None:
        return '%d %s' % (status_no, httplib.responses[status_no])
    
    # Can't find it... just hand it back.
    return status

def status_resolver(app):
    """WSGI middlewear which attempts to resolve whatever is sent as the
    status object into a proper HTTP status.
    
    """
    
    def inner(environ, start):
        def inner_start(status, headers):
            start(resolve_status(status), headers)
        return app(environ, inner_start)
    return inner

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
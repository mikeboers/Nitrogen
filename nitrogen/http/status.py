"""Module for WSGI status helping functions."""

from __future__ import absolute_import

import sys
import re
import logging
from httplib import responses as _code_to_message

from paste.httpexceptions import *
from paste.httpexceptions import make_middleware

from nitrogen.webio.headers import Headers

log = logging.getLogger(__name__)


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
    def _status_resolver(environ, start):
        log('Status_resolver has been deprecated.')
        return app(environ, start)
    return _status_resolver




def not_found_catcher(app, render):
    """Displays the _404.tpl template along with a "404 Not Found" status if a
    HTTPNotFound is thrown within the app that it wraps. This error is
    normally thrown by routers.
    """
    def not_found_catcher_app(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except HTTPNotFound as e:
            log.info('caught HTTPNotFound: %r' % e.detail)
            start('404 Not Found', [('Content-Type', 'text/html')])
            yield render('_404.tpl')
    return not_found_catcher_app


def catch_any_status(app):
    def _catch_any_status(environ, start):
        app_iter = []
        try:
            app_iter = iter(app(environ, start))
            yield next(app_iter)
        except HTTPException, e:
            if isinstance(e, HTTPRedirection):
                headers = Headers(e.headers)
                log.info('caught %d %s (to %r): %r' % (e.code, e.title, headers['location'], e.detail))
            else:
                log.info('caught %d %s: %r' % (e.code, e.title, e.detail))
            for x in e(environ, start):
                yield x
            return
        else:
            for x in app_iter:
                yield x
            
    return _catch_any_status




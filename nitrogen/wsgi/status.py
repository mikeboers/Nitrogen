import httplib

def resolve_status(status):
    """Resolve a given object into the status that it should represent.
    
    Examples:
        >>> _resolve_status(200)
        '200 OK'
        >>> _resolve_status(404)
        '404 Not Found'
        >>> _resolve_status('UNAUTHORIZED')
        '401 Unauthorized'
        >>> _resolve_status(None)
        '200 OK'
        >>> _resolve_status('314159 Not in list')
        '314159 Not in list'
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
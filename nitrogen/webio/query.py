
import multimap

from ..uri.query import Query

ENVIRON_KEY = 'nitrogen.get'

def parse_query(environ, charset=None, errors=None, key=ENVIRON_KEY):
    """Return the query for this request."""
    if key not in environ:
        environ[key] = Query(environ.get('QUERY_STRING', ''), charset=charset, decode_errors=errors)
    return environ[key]

import multimap

from ..uri.query import Query

ENVIRON_KEY = 'nitrogen.get'

def parse_query(environ, key=ENVIRON_KEY):
    """Return the query for this request."""
    if key not in environ:
        environ[key] = Query(environ.get('QUERY_STRING', ''))
    return environ[key]
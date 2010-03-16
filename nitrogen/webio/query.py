
import multimap

from ..uri.query import Query

ENVIRON_KEY = 'nitrogen.get'

def parse_query(environ, key=ENVIRON_KEY):
    """Get the query string parsed into a MultiMap.
    
    This multimap is lazily parsed when it is actually accessed. It is also
    cached in the environment, so changes to one will be reflected to later
    results of this function.
    
    """
    if key not in environ:
        def parse_query_generator():
            query = environ.get('QUERY_STRING', '')
            return Query(query).allitems()
        environ[key] = multimap.DelayedMultiMap(parse_query_generator)
    return environ[key]
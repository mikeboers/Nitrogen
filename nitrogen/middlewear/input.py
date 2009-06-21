"""Module for middlewear that will parse GET, POST, posted files, and basic cookies."""

import cgi
import collections
    
try:
    from ..uri.query import Query
    from ..cookie import Container as CookieContainer
except ValueError:
    import sys
    sys.path.insert(0, '..')
    from uri.query import Query
    from cookie import Container as CookieContainer






if __name__ == '__main__':
    from test import run
    run()
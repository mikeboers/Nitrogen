
from __future__ import absolute_import

from rfc822 import parsedate_tz
from datetime import datetime
from time import mktime

def parse_http_time(x):
    """
    
    >>> http_time = 'Sun, 15 Nov 2009 17:06:03 EST'
    >>> dt = parse_http_time(http_time)
    >>> dt
    datetime.datetime(2009, 11, 15, 22, 6, 3)
    
    """
    raw = parsedate_tz(x)
    timestamp = mktime(raw[:9])
    timestamp -= raw[9]
    return datetime.fromtimestamp(timestamp)


def format_http_time(dt):
    """
    
    >>> http_time = 'Sun, 15 Nov 2009 17:06:03 EST'
    >>> dt = parse_http_time(http_time)
    >>> format_http_time(dt)
    'Sun, 15 Nov 2009 22:06:03 UTC'
    
    """
    return dt.strftime("%a, %d %b %Y %H:%M:%S UTC")


if __name__ == '__main__':
    import doctest
    doctest.testmod()
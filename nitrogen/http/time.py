
from __future__ import absolute_import

from rfc822 import parsedate_tz
from datetime import datetime, timedelta
from time import mktime

def parse_http_time(x):
    """
    
    >>> http_time = 'Sun, 15 Nov 2009 17:06:03 EST'
    >>> dt = parse_http_time(http_time)
    >>> dt
    datetime.datetime(2009, 11, 15, 22, 6, 3)
    
    >>> parse_http_time('clearly wrong')
    Traceback (most recent call last):
    ...
    ValueError: could not parse time 'clearly wrong'
    
    >>> parse_http_time('Sun, 56 Nov 2009 17:06:03 EST')
    Traceback (most recent call last):
    ...
    ValueError: 'Sun, 56 Nov 2009 17:06:03 EST' is not a valid date
    
    >>> parse_http_time('Sat, 28 Feb 2009 01:23:45 UTC')
    datetime.datetime(2009, 2, 28, 1, 23, 45)
    
    >>> parse_http_time('Sun, 29 Feb 2009 01:23:45 UTC')
    Traceback (most recent call last):
    ...
    ValueError: 'Sun, 29 Feb 2009 01:23:45 UTC' is not a valid date
    
    >>> parse_http_time('Sun, 29 Feb 2008 01:23:45 UTC')
    datetime.datetime(2008, 2, 29, 1, 23, 45)
    
    """
    
    raw = parsedate_tz(x)
    if not raw:
        raise ValueError('could not parse time %r' % x)
    
    # Before and after are tuples of year, month, day, hour, minute, second.
    # parsedate_tz does not check to make sure things are in range (ie. you
    # could have a 56th of November), but mktime does make the nessesary
    # adjustments. So we are comparing the year/month/day breakdown of the
    # time to make sure it isn't changing. If it does, we throw a ValueError.
    before = raw[:6]
    timestamp = mktime(raw[:9])
    dt = datetime.fromtimestamp(timestamp)
    after = tuple(dt.utctimetuple())[:6]
    if before != after:
        raise ValueError('%r is not a valid date' % x)
    
    # Apply the timezone difference.
    dt -= timedelta(seconds=raw[9])
    
    return dt


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
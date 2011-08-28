import datetime
import re

from markupsafe import Markup as Literal

from ..uri.query import encode as _qe


def query_encode(x='', **kwargs):
    if kwargs:
        x = kwargs
    if isinstance(x, dict):
        x = x.items()
    if isinstance(x, (list, tuple)):
        return '&'.join('%s=%s' % (_qe(str(k)), _qe(str(v))) for k, v in x)
    return _qe(x)


def fuzzy_time(d, now=None):
    now = now or datetime.datetime.utcnow()
    diff = now - d
    s = diff.seconds + diff.days * 24 * 3600
    future = s < 0
    days, s = divmod(abs(s), 60 * 60 * 24)
    prefix = 'in ' if future else ''
    postfix = '' if future else ' ago'
    if days > 7:
        return 'on ' + d.strftime('%B %d, %Y')
    elif days == 1:
        out = '1 day'
    elif days > 1:
        out = '{0} days'.format(diff.days)
    elif s <= 1:
        return 'just now'
    elif s < 60:
        out = '{0} seconds'.format(s)
    elif s < 3600:
        out = '{0} minutes'.format(s/60)
    else:
        out = '{0} hours'.format(s/3600)
    return prefix + out + postfix


def urlify_name(name):
    """Converts a name or title into something we can put into a URI.
    
    This is designed to only be for one way usage (ie. we can't use the
    urlified names to figure out what photo or photoset we are talking about).
    """
    return re.sub(r'\W+', '-', name).strip('-')


nl2br = lambda s: re.sub(r'\n{3,}', '\n\n', s).replace("\n", "<br />")
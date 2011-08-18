"""nitrogen.view.defaults

This module contains default values for use with view environments. Currently
it only contains a `context` dict, which will be used as a starting point for
the `globals` attribute on a view environment.

It contains a number of functions and helpers that we tend to use all over the
place.

"""


import json
import pprint
import random
import re
import datetime

import webhelpers.text
import webhelpers.html
from markdown import markdown

from ..markdown import markdown
from ..uri.query import encode as query_encode
from .util import urlify_name, clean_html, smart_html_escape


context = {}

context['repr'] = repr
context['sorted'] = sorted
context['html_escape'] = smart_html_escape
context['h'] = smart_html_escape

context['json'] = json.dumps
context['markdown'] = markdown
context['format_date'] = lambda d, f: (d.strftime(f) if d else '')
context['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
context['nl2br'] = lambda s: re.sub(r'\n{3,}', '\n\n', s).replace("\n", "<br />")

context['pformat'] = pprint.pformat

context['truncate'] = webhelpers.text.truncate
context['html'] = webhelpers.html.HTML

context['urlify_name'] = urlify_name
context['clean_html'] = clean_html


context['q'] = query_encode
context['query_encode'] = query_encode


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

context['fuzzy_time'] = fuzzy_time

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
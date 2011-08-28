from __future__ import absolute_import

import json
import pprint
import random
import re
import datetime

from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException
from mako.template import Template

from .markdown import markdown
from .util import urlify_name, fuzzy_time, nl2br, query_encode


defaults = {}

defaults['markdown'] = markdown
defaults['json'] = json.dumps
defaults['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
defaults['nl2br'] = nl2br
defaults['pformat'] = pprint.pformat
defaults['urlify_name'] = urlify_name
defaults['fuzzy_time'] = fuzzy_time

defaults['query_encode'] = query_encode
defaults['q'] = query_encode




def _inline_callback(m):
    statement = m.group(1).strip()
    return '\\\n%% %s%s\n' % (statement, '' if statement.startswith('end') else ':')

_inline_re = re.compile(r'%{([^}]+)}')

def inline_control_statements(source):
    return _inline_re.sub(_inline_callback, source)

_post_white_re = re.compile(r'([$%]){(.*?)-}\s*')
_pre_white_re = re.compile(r'\s*([$%]){-(.*?)}')
def whitespace_control(source):
    source = _post_white_re.sub(r'\1{\2}', source)
    return _pre_white_re.sub(r'\1{\2}', source)
from __future__ import absolute_import

import json
import pprint
import random
import re
import datetime

from mako.lookup import TemplateLookup
from mako.exceptions import TopLevelLookupException
from mako.template import Template
from mako.filters import  xml_escape, html_escape, url_escape
from .markdown import markdown
from .util import urlify_name, fuzzy_time, nl2br, query_encode
from markupsafe import Markup, escape


class ReverseDefaultFilters(list):
    def __add__(self, other):
        return other + list(self)


defaults = {}

defaults['markdown'] = markdown
defaults['json'] = json.dumps
defaults['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
defaults['nl2br'] = nl2br
defaults['pformat'] = pprint.pformat
defaults['urlify_name'] = urlify_name
defaults['fuzzy_time'] = fuzzy_time

defaults['h'] = defaults['html_escape'] = html_escape
defaults['x'] = defaults['xml_escape'] = xml_escape
defaults['u'] = defaults['url_escape'] = url_escape

defaults['q'] = defaults['query_escape'] = defaults['query_encode'] = query_encode



_inline_control_re = re.compile(r'%{([^}]+)}')
def _inline_callback(m):
    statement = m.group(1).strip()
    return '\\\n%% %s%s\n' % (statement, '' if statement.startswith('end') else ':')
def inline_control_statements(source):
    return _inline_control_re.sub(_inline_callback, source)

_post_white_re = re.compile(r'([$%]){(.*?)-}\s*')
_pre_white_re = re.compile(r'\s*([$%]){-(.*?)}')
def whitespace_control(source):
    source = _post_white_re.sub(r'\1{\2}', source)
    return _pre_white_re.sub(r'\1{\2}', source)

_tiny_mako_re = re.compile(r'([$%]{.*?}|<%1? .*?%>)')
def tiny_mako(source):
    parts = _tiny_mako_re.split(source)
    for i in range(0, len(parts), 2):
        parts[i] = parts[i] and ('<%%text>%s</%%text>' % parts[i])
    return ''.join(parts)

from __future__ import absolute_import

import json
import pprint
import random
import re
import datetime
import collections
import threading

from mako.lookup import TemplateLookup as BaseTemplateLookup
from mako.exceptions import TopLevelLookupException
from mako.template import Template
from mako.filters import  xml_escape, html_escape, url_escape
from mako.runtime import Context as BaseContext
from markupsafe import Markup, escape

import haml

from .markdown import markdown
from .util import urlify_name, fuzzy_time, nl2br, query_encode


# We need to create our own version of the mako.TemplateLookup so that we can
# have different preprocessors for each file extension. If we have different
# lookups for each file extension then those preprocessors will apply to the
# entire inheritance chain, which is not acceptable as we are currently using a
# mix of HAML and plain mako.
class TemplateLookup(BaseTemplateLookup):

    def __init__(self, *args, **kwargs):
        self.preprocessors_by_ext = kwargs.pop('preprocessors_by_ext', [])
        super(TemplateLookup, self).__init__(*args, **kwargs)
        self.__mutex = threading.RLock()

    def _load(self, filename, uri):

        # Apply the preprocessors for this specific filetype.
        for file_ext, preprocessor in self.preprocessors_by_ext:
            if not filename.endswith(file_ext):
                continue

            # Need to work inside of a recursive lock so that threads don't
            # trample what we are doing to the lookup state.
            self.__mutex.acquire()
            existing = self.template_args['preprocessor']
            self.template_args['preprocessor'] = preprocessor
            try:
                template = super(TemplateLookup, self)._load(filename, uri)
            finally:
                # Make sure to set the original setting back.
                self.__mutex.release()
                self.template_args['preprocessor'] = existing
            return template
        
        # Fall back onto the default.
        return super(TemplateLookup, self)._load(filename, uri)
 


class Buffer(object):
 
    def __init__(self):
        self.data = collections.deque()
 
    def truncate(self):
        self.data = collections.deque()
        
    def write(self, x):
        self.data.append(unicode(x))
 
    def getvalue(self):
        return u''.join(self.data)


class Context(BaseContext):
    
    def _push_writer(self):
        """push a capturing buffer onto this Context and return
        the new writer function."""
 
        buf = Buffer()
        self._buffer_stack.append(buf)
        return buf.write


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


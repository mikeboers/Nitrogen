import logging
import re
import cgi

import mako.filters


log = logging.getLogger(__name__)


class Literal(unicode):
    def __unicode__(self):
        return self

original_html_escape = mako.filters.html_escape

def smart_html_escape(x):
    if isinstance(x, Literal):
        return x
    return original_html_escape(x)

# XXX: MONKEY PATCHING!!!!!
mako.filters.html_escape = smart_html_escape

def clean_html(html):
    """Asserts the "cleanliness" of html. Closes tags, indents, etc."""
    log.warning('clean_html has been depreciated')
    return html
    # return BeautifulSoup(html).prettify().decode('utf8')


def urlify_name(name):
    """Converts a name or title into something we can put into a URI.
    
    This is designed to only be for one way usage (ie. we can't use the
    urlified names to figure out what photo or photoset we are talking about).
    """
    return re.sub(r'\W+', '-', name).strip('-')


# preprocessors

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
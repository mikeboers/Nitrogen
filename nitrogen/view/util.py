

import re

from BeautifulSoup import BeautifulSoup


class Markup(unicode):
    pass

def html_escape(x):
    if isinstance(x, Markup):
        return x
    return cgi.escape(x, True)

def clean_html(html):
    """Asserts the "cleanliness" of html. Closes tags, indents, etc."""
    return BeautifulSoup(html).prettify().decode('utf8')


def urlify_name(name):
    """Converts a name or title into something we can put into a URI.
    
    This is designed to only be for one way usage (ie. we can't use the
    urlified names to figure out what photo or photoset we are talking about).
    """
    return re.sub(r'\W+', '-', name).strip('-')
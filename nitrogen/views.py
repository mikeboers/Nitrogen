'''Template module for Pix Ray website.'''

import os
import json
import datetime
import random

try:
    from .lib import jinja2 as jinja
    from .lib.markdown import markdown
    from .lib.BeautifulSoup import BeautifulSoup
except ValueError:
    import lib.jinja2 as jinja
    from lib.markdown import markdown
    from lib.BeautifulSoup import BeautifulSoup

def clean_html(html):
    """Asserts the "cleanliness" of html. Closes tags and such."""
    return BeautifulSoup(html).prettify()

def build_environment(*paths):
    # setup a loader and environment
    loader = jinja.FileSystemLoader(paths)
    environment = jinja.Environment(
        loader=loader
    )

    # Setup nl2br and escape.
    # This could be done better. nl2br can be smart about working on Markup
    # objects so that we don't have to replace the built in escape filter.
    # The question then becomes, do I WANT to keep using the Markup objects?
    nl2br = lambda s: s.replace("\n", "<br />")
    escape = lambda s: unicode(jinja.escape(s))

    environment.filters['nl2br'] = nl2br
    environment.filters['escape'] = escape
    environment.filters['e'] = escape
    environment.filters['json'] = json.dumps
    environment.filters['markdown'] = lambda x: clean_html(markdown(x.encode('utf8'))).decode('utf8')
    environment.filters['format_date'] = lambda d, f: (d.strftime(f) if d else '')
    environment.filters['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
    environment.filters['sorted'] = sorted
    environment.filters['repr'] = repr
    
    return environment

def build_render(environ):
    def render(template_name, **data):
        '''Find a template file and render it with the given keyword arguments.'''
        template = environ.get_template(template_name)
        return template.render(**data)
    return render
    
def build_iter_render(environ):
    def iter_render(template_name, **data):
        '''Find a template file and render it with the given keyword arguments.'''
        template = environ.get_template(template_name)
        return template.generate(**data)
    return iter_render
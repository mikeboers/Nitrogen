'''Template module for Pix Ray website.'''

import os
import json
import datetime
import random

# Setup path for local evaluation.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])
    import nitrogen
    
import mako.template
import mako.lookup
import markdown
import BeautifulSoup

TYPE_HEADER_HTML = ('Content-Type', 'text/html;charset=UTF-8')
TYPE_HEADER_TEXT = ('Content-Type', 'text/plain;charset=UTF-8')

def clean_html(html):
    """Asserts the "cleanliness" of html. Closes tags and such."""
    return BeautifulSoup(html).prettify()

defaults = {}
defaults['nl2br'] = lambda s: s.replace("\n", "<br />")
defaults['json'] = json.dumps
defaults['markdown'] = lambda x: clean_html(markdown(x.encode('utf8'))).decode('utf8')
defaults['format_date'] = lambda d, f: (d.strftime(f) if d else '')
defaults['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
defaults['sorted'] = sorted
defaults['repr'] = repr

# TODO: Change the assumed path location. Move this into the configs.
paths = [os.path.abspath(__file__ + '/../../view')]
lookup = mako.lookup.TemplateLookup(directories=paths, input_encoding='utf-8')

def render(template_name, **data):
    '''Find a template file and render it with the given keyword arguments.'''
    template = lookup.get_template(template_name)
    data.update(defaults)
    return template.render_unicode(**data)

def render_string(template, **data):
    template = make.template.Template(template, lookup=lookup)
    data.update(defaults)
    return template.render_unicode(**data)
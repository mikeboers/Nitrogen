'''Template module for Pix Ray website.'''

import os
import json
import datetime
import random
import threading

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)
    
import mako.template
import mako.lookup
from markdown import markdown
from BeautifulSoup import BeautifulSoup

import webhelpers.text
import webhelpers.html
HTML = webhelpers.html.HTML

from . import environ, config, server

from models.textblob import TextBlob, MarkdownBlob
from models import session

TYPE_HEADER_HTML = ('Content-Type', 'text/html;charset=UTF-8')
TYPE_HEADER_TEXT = ('Content-Type', 'text/plain;charset=UTF-8')

def clean_html(html):
    """Asserts the "cleanliness" of html. Closes tags and such."""
    return BeautifulSoup(html).prettify()
    
local = threading.local()

def add_flash_message(class_, message):
    get_flash_messages().append((class_, message))

def get_flash_messages():
    if not hasattr(local, 'flash_messages'):
        local.flash_messages = []
    return local.flash_messages

def textblob(key, permission=None):
    blob = session.query(TextBlob).filter_by(key=key).first()
    if not blob:
        blob = TextBlob(key=key, value='JUST CREATED. Add some content!')
        session.add(blob)
        session.commit()
    return render('_textblob.tpl', blob=blob, permission=permission)

def markdownblob(key, permission=None):
    blob = session.query(MarkdownBlob).filter_by(key=key).first()
    if not blob:
        blob = MarkdownBlob(key=key, value='**JUST CREATED.** *Add some content!*')
        session.add(blob)
        session.commit()
    return render('_textblob_md.tpl', blob=blob, permission=permission)

def button(message, silk=None, href=None, id=None):
    pass
           
defaults = {}
defaults['nl2br'] = lambda s: s.replace("\n", "<br />")
defaults['json'] = json.dumps
defaults['markdown'] = lambda x: clean_html(markdown(x.encode('utf8'))).decode('utf8')
defaults['format_date'] = lambda d, f: (d.strftime(f) if d else '')
defaults['randomize'] = lambda x: sorted(x, key=lambda y: random.random())
defaults['sorted'] = sorted
defaults['repr'] = repr
defaults['textblob'] = textblob
defaults['textblob_md'] = markdownblob
defaults['truncate'] = webhelpers.text.truncate
defaults['html'] = HTML

lookup = mako.lookup.TemplateLookup(directories=config.template_path, input_encoding='utf-8')

def _set_defaults(data):
    data.update(defaults)
    try:
        data['is_admin_area'] = environ['SERVER_NAME'].startswith('admin.')
        data['user'] = environ['app.user']
        data['config'] = config
        data['environ'] = environ
        data['server'] = server
    except:
        pass
    data['flash_messages'] = get_flash_messages()
    
def render(template_name, **data):
    '''Find a template file and render it with the given keyword arguments.'''
    template = lookup.get_template(template_name)
    _set_defaults(data)
    return template.render_unicode(**data)

def render_string(template, **data):
    template = make.template.Template(template, lookup=lookup)
    _set_defaults(data)
    return template.render_unicode(**data)
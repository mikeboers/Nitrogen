'''Template module for Pix Ray website.'''

import os
import json
import datetime
import random
import threading
import logging
import re


    
import mako.template
import mako.lookup
from markdown import markdown
from BeautifulSoup import BeautifulSoup

import webhelpers.text
import webhelpers.html
HTML = webhelpers.html.HTML

from models.textblob import TextBlob, MarkdownBlob
from models.meta import meta as modelmeta

from meta import meta as view_meta

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


def urlify_name(name):
    """Converts a name or title into something we can put into a URI.

    This is designed to only be for one way usage (ie. we can't use the
    urlified names to figure out what photo or photoset we are talking about).
    """
    return re.sub(r'\W+', '-', name).strip('-')
               


def _set_defaults(data):
    data.update(defaults)
    data['is_admin_area'] = environ['SERVER_NAME'].startswith('admin.')
    data['config'] = config
    data['environ'] = environ
    data['server'] = server
    data['user'] = environ.get('app.user')
    data['flash_messages'] = get_flash_messages()


render = view_meta.render()
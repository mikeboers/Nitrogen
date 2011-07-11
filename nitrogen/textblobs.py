
from __future__ import absolute_import

import logging

from sqlalchemy import *
from sqlalchemy.exc import NoSuchTableError

from .app import build_inheritance_mixin_class
from .crud import CRUD
from .forms import *


log = logging.getLogger(__name__)


class TextBlobAppMixin(object):
    
    textblob_template = '/textblob.html'
    
    def __init__(self, *args, **kwargs):
        super(TextBlobAppMixin, self).__init__(*args, **kwargs)
        
        try:
            class Mixin(self.Base):
                __table__ = Table('textblobs', self.metadata, autoload=True)
                _app = self
            self.TextBlob = build_inheritance_mixin_class(self.__class__, Mixin, 'TextBlob')
            
        except NoSuchTableError:
            log.warning('Table does not exist. Please upgrade database.')
            self.TextBlob = None
        
        class MarkdownForm(self.Form):
            content = MarkdownField('Content')

        class PlainForm(self.Form):
            content = TextField('Content')

        class HtmlForm(self.Form):
            content = TextAreaField('Content')
    
        self.route('/__textblob/markdown', self.CRUD(
            render=self.render,
            Session=self.Session,
            form_class=MarkdownForm,
            model_class=self.TextBlob,
            partial=self.textblob_template,
            partial_key='blob',
            partial_kwargs={'type_':'markdown'}
        ))

        self.route('/__textblob/html', self.CRUD(
            render=self.render,
            Session=self.Session,
            form_class=HtmlForm,
            model_class=self.TextBlob,
            partial=self.textblob_template,
            partial_key='blob',
            partial_kwargs={'type_':'html'}
        ))

        self.route('/__textblob/text', self.CRUD(
            render=self.render,
            Session=self.Session,
            form_class=PlainForm,
            model_class=self.TextBlob,
            partial=self.textblob_template,
            partial_key='blob',
            partial_kwargs={'type_':'text'}
        ))
        
        self.view_globals.update(
            textblob=self.textblob
        )
    
    
    def textblob(self, name, type=None, predicate=None):

        s = self.Session()
        blob = s.query(self.TextBlob).filter_by(name=name).first()
        if not blob:
            blob = self.TextBlob(name=name, content='JUST CREATED! Add some content...')
            s.add(blob)
            s.commit()
        return self.render('/textblob.html', blob=blob, type_=type,
            predicate=predicate
        )
    












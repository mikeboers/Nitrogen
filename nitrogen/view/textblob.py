

import datetime

from sqlalchemy import *

from ..editable import Editable
from ..model.form import MarkdownRenderer

def build_textblob_functions(engine, session, Form, Base, render):
    
    class TextBlob(Base):
        __tablename__ = 'textblobs'
        id = Column(Integer, primary_key=True)
        key = Column(Text, nullable=False)
        value = Column(Text, nullable=False)

    class MarkdownBlob(Base):
        __tablename__ = 'markdownblobs'
        id = Column(Integer, primary_key=True)
        key = Column(Text, nullable=False)
        value = Column(Text, nullable=False)
    

    
    TextBlob.__table__.create(engine, checkfirst=True)
    MarkdownBlob.__table__.create(engine, checkfirst=True)

    textblob_fieldset = Form(TextBlob)
    textblob_fieldset.configure(include=[textblob_fieldset.value], options=[
        # textblob_fieldset.value.with_renderer(formalchemy.fields.TextAreaFieldRenderer)
    ])

    markdownblob_fieldset = Form(MarkdownBlob)
    markdownblob_fieldset.configure(include=[
        markdownblob_fieldset.value
    ], options=[
        markdownblob_fieldset.value.with_renderer(MarkdownRenderer)
    ])
    
    textblob_editable = Editable(
        session=session,
        render=render,
        model=TextBlob,
        form=textblob_fieldset,
        partial='_textblob.tpl',
        partial_key='blob'
    )
    
    markdownblob_editable = Editable(
        session=session,
        render=render,
        model=MarkdownBlob,
        form=markdownblob_fieldset,
        partial='_textblob_md.tpl',
        partial_key='blob'
    )
    
    def textblob(key):
        blob = session.query(TextBlob).filter_by(key=key).first()
        if not blob:
            blob = TextBlob(key=key, value='JUST CREATED. Add some content!')
            session.add(blob)
            session.commit()
        return render('_textblob.tpl', blob=blob)

    def markdownblob(key):
        blob = session.query(MarkdownBlob).filter_by(key=key).first()
        if not blob:
            blob = MarkdownBlob(key=key, value='**JUST CREATED.** *Add some content!*')
            session.add(blob)
            session.commit()
        return render('_textblob_md.tpl', blob=blob)
    
    return textblob, textblob_editable, markdownblob, markdownblob_editable
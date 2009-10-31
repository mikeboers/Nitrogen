import datetime

from sqlalchemy import *

from base import Base
from forms import FieldSet, MarkdownRenderer

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

# TextBlob.__table__.create(engine, checkfirst=True)
# MarkdownBlob.__table__.create(engine, checkfirst=True)

textblob_fieldset = FieldSet(TextBlob)
textblob_fieldset.configure(include=[textblob_fieldset.value], options=[
    # textblob_fieldset.value.with_renderer(formalchemy.fields.TextAreaFieldRenderer)
])

markdownblob_fieldset = FieldSet(MarkdownBlob)
markdownblob_fieldset.configure(include=[
    markdownblob_fieldset.value
], options=[
    markdownblob_fieldset.value.with_renderer(MarkdownRenderer)
])
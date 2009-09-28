# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen.model'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import datetime
from . import *

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
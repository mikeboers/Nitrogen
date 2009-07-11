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
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)

class MarkdownBlob(Base):
    __tablename__ = 'markdownblobs'
    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)

TextBlob.__table__.create(engine, checkfirst=True)
MarkdownBlob.__table__.create(engine, checkfirst=True)

text_fieldset = formalchemy.FieldSet(TextBlob)

markdown_fieldset = formalchemy.FieldSet(MarkdownBlob)
markdown_fieldset.configure(options=[
    markdown_fieldset.value.with_renderer(MarkdownRenderer)
])
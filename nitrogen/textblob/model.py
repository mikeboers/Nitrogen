
# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = name[:name.rfind('.py')]
        name = (name[:-8] if name.endswith('__init__') else name).rstrip(os.path.sep)
        name = name.replace(os.path.sep, '.')
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)


import datetime

from sqlalchemy import *

from base import Base
from fieldset import FieldSet, MarkdownRenderer

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
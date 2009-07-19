# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen.model'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import logging

from .. import config

from sqlalchemy import *
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, MutableType
from sqlalchemy.orm.attributes import instance_state

Base = declarative_base()

engine = create_engine(config.database_uri)
Session = orm.sessionmaker(bind=engine)
session = orm.scoped_session(Session)

logger = logging.getLogger('sqlalchemy')
logger.setLevel(1000)

### {
# Monkey patching the declarative base to add some convenience features, such
# as per-instance session attributs, delete methods, etc.

@property
def _Base_session(self):
    return orm.object_session(self)
Base.session = _Base_session

def _Base_delete(self):
    self.session.delete(self)
Base.delete = _Base_delete

def _Base_mark_dirty(self):
    self.session.dirty.add(self)
    # instance_state(self).modified = True
Base.mark_dirty = _Base_mark_dirty

### }

from forms import *








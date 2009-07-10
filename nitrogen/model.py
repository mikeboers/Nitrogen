# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])
    __package__ = 'nitrogen'
    __import__(__package__)

from nitrogen import config

from sqlalchemy import *
import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator
    
Base = declarative_base()

engine = create_engine(config.database_uri, echo=config.database_log)
Session = orm.sessionmaker(bind=engine)
session = orm.scoped_session(Session)

### {
# Monkey patching the declarative base to add some convenience features, such
# as per-instance session attributs, delete methods, etc.

@property
def _Base_session(self):
    return object_session(self)
Base.session = _Base_session

def _Base_delete(self):
    self.session.delete(self)
Base.delete = _Base_delete

### }








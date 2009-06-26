
try:    
    from .lib.sqlalchemy import *
    from .lib.sqlalchemy.orm import sessionmaker, object_session, relation, backref
    from .lib.sqlalchemy.ext.declarative import declarative_base
except ValueError:
    import sys
    sys.path.append('lib')
    from sqlalchemy import *
    from sqlalchemy.orm import sessionmaker, object_session, relation, backref
    from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Monkey patching the declarative base to add some convenience features, such
# as per-instance session attributs, delete methods, etc.

@property
def _Base_session(self):
    return object_session(self)
Base.session = _Base_session

def _Base_delete(self):
    self.session.delete(self)
Base.delete = _Base_delete








"""Monkey-patched declarative base for models."""

import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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





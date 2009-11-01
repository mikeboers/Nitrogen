"""Monkey-patched declarative base for models."""

import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base

@property
def _Base_session(self):
    return orm.object_session(self)

def _Base_delete(self):
    self.session.delete(self)

def _Base_mark_dirty(self):
    self.session.dirty.add(self)
    # instance_state(self).modified = True

def build_base(metadata=None):
    Base = declarative_base(metadata=metadata)
    Base.session = _Base_session
    Base.delete = _Base_delete
    Base.mark_dirty = _Base_mark_dirty
    return Base



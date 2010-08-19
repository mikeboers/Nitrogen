"""Monkey-patched declarative base for models."""

import sqlalchemy.orm as orm
from sqlalchemy.ext.declarative import declarative_base as _declarative_base

@property
def _Base_session(self):
    """Get the session this object is associate with."""
    return orm.object_session(self)

def _Base_delete(self):
    """Delete this object from it's session."""
    self.session.delete(self)

def _Base_mark_dirty(self):
    """Mark this object dirty in it's session."""
    self.session.dirty.add(self)

def _Base_expire(self, attribute_names=None):
    """Expire this object's attributes."""
    self.session.expire(self, attribute_names)
 
def _Base_refresh(self, attribute_names=None):
    """Refresh this object's attributes immediately."""
    self.session.refresh(self, attribute_names)
       
def _Base_expunge(self):
    """Expunge this object from it's session."""
    self.session.expunge(self)

def declarative_base(metadata=None):
    Base = _declarative_base(metadata=metadata)
    Base.session    = _Base_session
    Base.delete     = _Base_delete
    Base.mark_dirty = _Base_mark_dirty
    Base.expunge    = _Base_expunge
    Base.expire     = _Base_expire
    Base.refresh    = _Base_refresh
    return Base



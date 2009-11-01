"""Monkey-patched declarative base for models."""

# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = '.'.join(name[:-3].split(os.path.sep)[:-1])
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)

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



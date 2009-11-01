
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


import logging

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .base import build_base

class ModelEnviron(object):
    
    def __init__(self, name=None, engine=None):
        self.name = str(name or id(self))
        self.log = logging.getLogger('%s?env=%s' % (__name__, self.name))
        
        self.engine = None
        self.Session = sessionmaker()
        self.session = scoped_session(self.Session)
        self.metadata = MetaData()
        self.Base = build_base(metadata=self.metadata)
        
        if engine:
            self.setup(engine)
    
    def setup(self, engine):
        if isinstance(engine, basestring):
            engine = create_engine(engine)
        self.engine = engine
        self.Session.configure(bind=engine)

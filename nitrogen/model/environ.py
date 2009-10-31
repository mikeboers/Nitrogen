# Everything in this module will be setup and/or bound to an engine when
# setup_meta is called from the models package.

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

class ModelEnviron(object):
    
    def __init__(self, engine=None):
        self.engine = None
        self.Session = sessionmaker()
        sels.session = scoped_session(Session)
        self.metadata = MetaData()
        
        if engine:
            self.setup(engine)
    
    def setup(self, engine):
        if isinstance(engine, basestring):
            engine = create_engine(engine)
        self.engine = engine
        self.Session.configure(bind=engine)

# Setup a global one.
environ = ModelEnviron()
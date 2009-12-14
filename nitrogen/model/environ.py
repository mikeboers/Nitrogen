

import logging

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .base import build_declarative_base

class ModelEnviron(object):
    
    def __init__(self, name=None, engine=None):
        self.name = str(name or id(self))
        self.log = logging.getLogger('%s?env=%s' % (__name__, self.name))
        
        self.engine = None
        self.Session = sessionmaker(autoflush=True)
        self.session = scoped_session(self.Session)
        self.metadata = MetaData()
        self.Base = build_declarative_base(metadata=self.metadata)
        
        if engine:
            self.bind(engine)
    
    def bind(self, engine):
        if isinstance(engine, basestring):
            engine = create_engine(engine)
        self.engine = engine
        self.Session.configure(bind=engine)
    
    def create_tables(self):
        self.metadata.create_all(self.engine)
    
    def wsgi_reset(self, app):
        def ModelEnviron_wsgi_reset_app(environ, start):
            for x in app(environ, start):
                yield x
            self.session.close()
        return ModelEnviron_wsgi_reset_app

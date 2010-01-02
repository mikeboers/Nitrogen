"""Module for the ModelEnviron class."""

import logging
import threading

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .base import build_declarative_base

class ModelEnviron(object):
    """A helper to contain the basic parts of a database connections.
    
    Attrs:
        engine
        metadata
        Base -- declarative base class
        Session -- session constructor
        session -- global thread-local session
    
    """
    
    def __init__(self, engine=None):
        """Initialize the environment.
        
        Args:
            engine -- The engine or string to bind to.
        
        """
        
        self.log = logging.getLogger('%s?id=%s' % (__name__, id(self)))
        
        self._local_sessions = []
        
        self.engine = None
        self.Session = sessionmaker(autoflush=True)
        self.session = self.local_session()
        self.metadata = MetaData()
        self.Base = build_declarative_base(metadata=self.metadata)
        
        if engine:
            self.bind(engine)
    
    def bind(self, engine):
        """Bind to an engine or string."""
        if isinstance(engine, basestring):
            engine = create_engine(engine)
        self.engine = engine
        self.Session.configure(bind=engine)
    
    def create_tables(self):
        """Create all the tables associated with this environ."""
        self.metadata.create_all(self.engine)
    
    def local_session(self):
        """Build a new thread-local session object.
        
        Every call to this method will return an object which acts on unique
        sessions (by thread). Ie. Two sessions from this method in the same
        thread will be different from each other.
        
        This should not be called on a request-basis. This is mainly for other
        environ contructs to have their own thread-local local session.
        
        """
        
        s = scoped_session(self.Session)
        self._local_sessions.append(s)
    
    def wsgi_reset(self, app):
        """Reset all the thread-local sessions generated."""
        def ModelEnviron_wsgi_reset_app(environ, start):
            for x in app(environ, start):
                yield x
            for s in self._local_sessions:
                s.close()
        return ModelEnviron_wsgi_reset_app

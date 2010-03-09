"""Module for the ModelContext class."""

import logging
import threading

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

from .declarative import declarative_base
from .session import Session


class ModelContext(object):
    """A helper to contain the basic parts of a database connections.
    
    By default this also uses the nitrogen extended Session (with locking) and
    declarative Base (with extra session functions).
    
    Attributes:
        engine
        metadata
        Base -- declarative base class
        Session -- session constructor
        session -- global thread-local session
    
    """
    
    def __init__(self, bind=None, autocommit=False, echo=False):
        """Initialize the environment.
        
        Args:
            bind -- The engine or string to bind to.
            autocommit -- sessionmaker kwarg autocommit.
            echo -- create_engine kwarg echo.
        
        """
        
        self.log = logging.getLogger('%s?id=%s' % (__name__, id(self)))
        
        self._local_sessions = []
        
        self.engine = None
        self.Session = sessionmaker(class_=Session, autocommit=autocommit, autoflush=True)
        self.session = self.local_session()
        self.metadata = MetaData()
        self.Base = declarative_base(metadata=self.metadata)
        self.echo = echo
        
        if bind:
            self.bind(bind)
    
    def bind(self, engine):
        """Bind to an engine or string."""
        if isinstance(engine, basestring):
            engine = create_engine(engine, echo=self.echo)
        self.engine = engine
        self.metadata.bind = engine
        self.Session.configure(bind=engine)
    
    def create_tables(self):
        """Create all the tables associated with this context."""
        self.metadata.create_all(self.engine)
    
    def local_session(self):
        """Build a new thread-local session object.
        
        Every call to this method will return an object which acts on unique
        sessions (by thread). Ie. Two sessions from this method in the same
        thread will be different from each other.
        
        This should not be called on a request-basis. This is mainly for other
        context-like contructs to have their own thread-local session.
        
        """
        
        s = scoped_session(self.Session)
        self._local_sessions.append(s)
        return s
    
    def wsgi_fixtures(self, app):
        """WSGI middleware to setup/teardown the model context per request.
        
        Currently resets the thread-local sessions generated
        
        """
        def ModelContext_wsgi_fixtures_app(environ, start):
            for x in app(environ, start):
                yield x
            for s in self._local_sessions:
                s.close()
                # Lets be even more aggresive... It seems that MAYBE a session
                # would persist when using flup thread pools.
                s.remove()
        return ModelContext_wsgi_fixtures_app
    
    def wsgi_reset(self, app):
        # Warn that we have changed the name. This can be removed once
        # all my web apps have moved on.
        msg = '%s.wsgi_reset is depreciated.' % self.__class__.__name__
        try:
            raise DepreciationWarning(msg)
        except DepreciationWarning:
            self.log.warning(msg, exc_info=sys.exc_info()))
        return self.wsgi_fixtures(app)

"""Module for the ModelContext class."""

import logging
import threading
import sys

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from .declarative import declarative_base
from .session import Session


class AppDBMixin(object):
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
    
    def __init__(self, *args, **kwargs):
        super(AppDBMixin, self).__init__(*args, **kwargs)
        
        self.engine = None
        self.Session = sessionmaker(class_=Session, autocommit=autocommit, autoflush=True)
        self.metadata = MetaData()
        self.Base = declarative_base(metadata=self.metadata)
    
    def bind(self, engine, echo=False):
        """Bind to an engine or string."""
        
        if isinstance(engine, basestring):
            engine = create_engine(engine, echo=echo)
            
        self.engine = engine
        self.metadata.bind = engine
        self.Session.configure(bind=engine)
    
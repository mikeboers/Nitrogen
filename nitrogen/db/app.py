"""Module for the ModelContext class."""

import logging
import threading
import sys

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker

from .declarative import declarative_base
from .session import Session



log = logging.getLogger(__name__)


class DBAppMixin(object):
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
        
        self.engine = None        
        self.Session = sessionmaker(class_=Session, autocommit=False, autoflush=True)
        self.metadata = MetaData()
        self.Base = declarative_base(metadata=self.metadata)
        
        super(DBAppMixin, self).__init__(*args, **kwargs)
        
        if self.config.db_bind:
            self.bind(self.config.db_bind, self.config.db_echo)
        else:
            self.bind('sqlite://', self.config.db_echo)
            log.warning('Bound to temporary database; please supply db_bind.')
    
    def export_to(self, map):
        super(DBAppMixin, self).export_to(map)
        map.update(
            engine=self.engine,
            Session=self.Session,
            metadata=self.metadata,
            Base=self.Base
        )
    
    def bind(self, engine, echo=False):
        """Bind to an engine or string."""
        
        if isinstance(engine, basestring):
            engine = create_engine(engine, echo=bool(echo))
            
        self.engine = engine
        self.metadata.bind = engine
        self.Session.configure(bind=engine)
    
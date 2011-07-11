"""Module for the ModelContext class."""

import logging

from sqlalchemy import MetaData, engine_from_config
from sqlalchemy.orm import sessionmaker

from .declarative import declarative_base
from .orm import Session


log = logging.getLogger(__name__)


class SQLAlchemyAppMixin(object):
    """A helper to contain the basic parts of a database connections.
    
    By default this also uses the nitrogen extended Session (with locking) and
    declarative Base (with extra session functions).
    
    Attributes:
        engine
        metadata
        Base -- declarative base class
        Session -- session constructor
    
    """
    
    def __init__(self, *args, **kwargs):
        super(SQLAlchemyAppMixin, self).__init__(*args, **kwargs)
        self.engine = engine_from_config(self.config, 'sqlalchemy_')
        self.Session = sessionmaker(
            autocommit=False,
            autoflush=True,
            bind=self.engine,
            class_=Session,
        )
        self.metadata = MetaData(bind=self.engine)
        self.Base = declarative_base(metadata=self.metadata)
    
    def setup_config(self):
        super(SQLAlchemyAppMixin, self).setup_config()
        if 'sqlalchemy_url' not in self.config:
            self.config['sqlalchemy_url'] = 'sqlite://'
            log.warning('Will bind to temporary database; please supply sqlalchemy_url.')
            
    def export_to(self, map):
        super(SQLAlchemyAppMixin, self).export_to(map)
        map.update(
            engine=self.engine,
            Session=self.Session,
            metadata=self.metadata,
            Base=self.Base
        )
    
    
# Everything in this module will be setup and/or bound to an engine when
# setup_meta is called from the models package.

from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import MetaData

from .base import Base

engine = None

Session = sessionmaker()
session = scoped_session(Session)

metadata = MetaData()

Base.metadata = metadata

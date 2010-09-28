from sqlalchemy import *
from migrate import *

metadata = MetaData()
    
table = Table('crud_versions', metadata,
    Column('id', Integer, primary_key=True),
    Column('object_type', Text, nullable=False),
    Column('object_id', Integer, nullable=False),
    Column('commit_time', DateTime, nullable=False),
    Column('data', Blob, nullable=False),
    Column('blame', Text, nullable=False),
    Column('comment', Text, nullable=False),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    metadata.bind = migrate_engine
    table.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    table.drop()

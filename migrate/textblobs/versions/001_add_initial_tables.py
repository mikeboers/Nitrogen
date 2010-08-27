from sqlalchemy import *
from migrate import *

metadata = MetaData()

table = Table('textblobs', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', Text, nullable=False),
    Column('content', Text, nullable=False),
)

def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind migrate_engine
    # to your metadata
    metadata.bind = migrate_engine
    table.create()

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    table.drop()

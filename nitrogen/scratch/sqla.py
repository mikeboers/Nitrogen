
import sys
sys.path.append('../lib')

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, object_session, relation, backref
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///:memory:', echo=False)
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Monkey patching the declarative base:

@property
def _Base_session(self):
    return object_session(self)
Base.session = _Base_session

def _Base_delete(self):
    self.session.delete(self)
Base.delete = _Base_delete

# Done monkey patching the declarative base.


class Person(Base):
    __tablename__ = 'persons'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    def __repr__(self):
        return '<Person:%s:%r>' % (self.name, self.emails)

class Email(Base):
    __tablename__ = 'emails'
    id = Column(Integer, primary_key=True)
    email = Column(String)
    
    person_id = Column(Integer, ForeignKey('persons.id'))
    person = relation(Person, backref='emails')
    
    def __repr__(self):
        return '<mailto:%s>' % self.email

Base.metadata.create_all(engine)

session = Session()

alice = Person(name='Alice')
alice.emails.append(Email(email='mail@example.com'))
alice.emails.append(Email(email='*@example.com'))

bob = Person(name='Bob')

session.add(alice)
session.add(bob)
session.commit()

session = Session()
for person in session.query(Person).all():
    print person

print Person.__table__.columns
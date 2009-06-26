
import sys
sys.path.append('../lib')

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, object_session

from elixir import *


metadata.bind = 'sqlite://'
metadata.bind.echo = False

_Entity = Entity
class SessionMixin(object):
    @property
    def session(self):
        return object_session(self)

class Food(Entity, SessionMixin):
    id = Field(Integer, primary_key=True)
    type = Field(String)
    name = Field(String)
    
    def __repr__(self):
        return '<Food:%s:%r>' % (self.type, self.name)

setup_all(True)


apple = Food(type='fruit', name="Apple")
session.commit()

print apple.session

for food in session.query(Food).all():
    print food
    food.delete()

session.commit()

print session.query(Food).all()
    
    
    

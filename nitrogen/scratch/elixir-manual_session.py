
import sys
sys.path.append('../lib')

from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, object_session

import elixir
elixir.session = None
from elixir import *

Session = sessionmaker()

metadata.bind = 'sqlite://'
metadata.bind.echo = False

class Food(Entity):
    id = Field(Integer, primary_key=True)
    type = Field(String)
    name = Field(String)
    
    def __repr__(self):
        return '<Food:%s:%r>' % (self.type, self.name)

setup_all(True)


session = Session()
apple = Food(type='fruit', name="Apple")
session.add(apple)
session.commit()

session = Session()
for food in session.query(Food).all():
    print food
    food.delete()

session.commit()

print session.query(Food).all()
    
    
    


from sqlalchemy import *

from cgi import escape

_default_builders = {}

def default_builder(sql_type):
    def inner(renderer):
        _default_builders[sql_type] = renderer
        return renderer
    return inner

def get_default_builder(sql_type):
    return _default_builders[sql_type]()

@default_builder(Text)
@default_builder(String)
class TextField(object):
    def __init__(self):
        pass
    
    def render(self, col):
        return '<input type="text" name="%s" />' % escape(col.name)

@default_builder(Integer)
class IntegerField(object):
    def render(self, col):
        return '<input type="text" name="%s" />' % escape(col.name)

@default_builder(Boolean)
class BooleanField(object):
    def render(self, col):
        return '<input type="checkbox" name="%s" />' % escape(col.name)

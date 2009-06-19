try:
    from .builder import get_default_builder
except:
    from builder import get_default_builder

class Column(object):
    
    def __init__(self, column):
        self.column = column
        self.name = column.name
        self.type = column.type
        self.renderer = get_default_builder(self.type.__class__)
    
    def __repr__(self):
        return '<FormColumn:%s>' % self.name

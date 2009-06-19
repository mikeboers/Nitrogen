try:
    from .column import Column
    from .form import Form
except ValueError:
    from column import Column
    from form import Form

class Model(object):
    
    def __init__(self, type):
        self.type = type
        self.columns = [Column(x) for x in self.type.table.columns]
        self.column_map = dict((x.name, x) for x in self.columns)
    
    def create(self, **kwargs):
        return Form(self, kwargs)

class Form(object):
    
    def __init__(self, model, data):
        self.model = model
        self.data = data
    
    def _render(self):
        yield '<ul>'
        for col in self.model.columns:
            yield '<li>'
            if col.renderer:
                yield col.renderer.render(col)
            else:
                yield 'NO RENDERER'
            yield '</li>'
        yield '</ul>'
    
    def render(self):
        return '\n'.join(self._render())

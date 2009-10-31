
import os
import threading

import mako.lookup

class ViewMeta(object):
    
    def __init__(self, path=None):
        path = path if path else []
        path.append(os.path.abspath(__file__ + '/../../templates'))
        self.lookup = mako.lookup.TemplateLookup(
            directories=path,
            input_encoding='utf-8'
        )
        self.path = self.lookup.directories
        self.defaults = {}
        self.local = threading.local()
    
    def _prep_data(self, data):
        data.update(self.defaults)
        data.update(self.local.__dict__)
    
    def render(self, template_name, **data):
        '''Find a template file and render it with the given keyword arguments.'''
        template = self.lookup.get_template(template_name)
        self._prep_data(data)
        return template.render_unicode(**data)
    
    # def render_string(self, template, **data):
    #     template = mako.template.Template(template, lookup=self.lookup)
    #     self._prep_data(data)
    #     return template.render_unicode(**data)

meta = ViewMeta()
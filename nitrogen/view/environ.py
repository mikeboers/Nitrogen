
# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = name[:name.rfind('.py')]
        name = (name[:-8] if name.endswith('__init__') else name).rstrip(os.path.sep)
        name = name.replace(os.path.sep, '.')
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)


import os
import threading
import logging

import mako.lookup

from defaults import context


class ViewEnviron(object):
    
    def __init__(self, name=None, path=None):
        self.name = str(name or id(self))
        self.log = logging.getLogger('%s?env=%s' % (__name__, self.name))
        
        if path and isinstance(path, basestring):
            path = [path]
        tmppath = path if path else []
        tmppath.append(os.path.abspath(__file__ + '/../../templates'))
        self.lookup = mako.lookup.TemplateLookup(
            directories=tmppath,
            input_encoding='utf-8'
        )
        self.path = self.lookup.directories
        self.context = context.copy()
        self.local = threading.local()
        
    def _prep_data(self, data):
        data.update(self.context)
        data.update(self.local.__dict__)
        data['flash_messages'] = self.flash_messages
        if hasattr(self.local, 'environ'):
            environ = self.local.environ
            data['is_admin_area'] = environ['SERVER_NAME'].startswith('admin.')
            data['user'] = environ.get('app.user')
    
    def render(self, template_name, **data):
        '''Find a template file and render it with the given keyword arguments.'''
        template = self.lookup.get_template(template_name)
        self._prep_data(data)
        return template.render_unicode(**data)
    
    def render_string(self, template, **data):
        template = mako.template.Template(template, lookup=self.lookup)
        self._prep_data(data)
        return template.render_unicode(**data)
    
    @property
    def flash_messages(self):
        if not hasattr(self.local, 'flash_messages'):
            self.local.flash_messages = []
        return self.local.flash_messages


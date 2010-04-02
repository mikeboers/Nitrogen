"""nitrogen.view.environ"""


import os
import threading
import logging

import mako.lookup

from .defaults import context
from .form import build_fieldset_class

class ViewContext(object):
    """Environment for working with views/templates.
    
    Attributes:
        log -- A logger, customized by the name argument to the contructor.
        path -- A list of paths to check when rendering.
        globals -- Context defaults that apply to all threads.
        locals -- Context defaults that apply to only the current thread.
    
    """
    
    def __init__(self, name=None, path=None):
        """Constructor.
        
        Parameters:
            name -- Used to specify which logger to use.
            path -- Initial list of paths to look for templates in.
        
        """
        
        self.name = str(name or id(self))
        self.log = logging.getLogger('%s?env=%s' % (__name__, self.name))
        self.FieldSet = build_fieldset_class(self.render)
        
        if path and isinstance(path, basestring):
            path = [path]
        path = path or []
        path.append(os.path.abspath(__file__ + '/../../templates'))
        self.lookup = mako.lookup.TemplateLookup(
            directories=path,
            input_encoding='utf-8'
        )
        self.path = self.lookup.directories
        
        self.globals = context.copy()
        self._local = threading.local()
    
    @property
    def locals(self):
        """Return the underlying dict of the thread-local object."""
        return self._local.__dict__
        
    def _prep_data(self, data):
        """Prepare user supplied data for use as a view context.
        
        Adds globals, locals, flash messages, etc.
        
        """
        
        data.update(self.globals)
        data.update(self.locals)
        data['flash_messages'] = self.flash_messages
        if hasattr(self._local, 'environ'):
            environ = self._local.environ
            data['is_admin_area'] = environ['SERVER_NAME'].startswith('admin.')
            data['user'] = environ.get('app.user')
    
    def render(self, template_name, **data):
        """Find a template file and render it with the given keyword args.
        
        Searches on the current `self.path`.
        
        """
        
        template = self.lookup.get_template(template_name)
        self._prep_data(data)
        return template.render_unicode(**data)
    
    def render_string(self, template, **data):
        """Render a string as a template with the given keyword args."""
        template = mako.template.Template(template, lookup=self.lookup)
        self._prep_data(data)
        return template.render_unicode(**data)
    
    @property
    def flash_messages(self):
        if not hasattr(self._local, 'flash_messages'):
            self._local.flash_messages = []
        return self._local.flash_messages
    
    def add_flash_message(self, class_, message):
        self.flash_messages.append((class_, message))
        
    def wsgi_setup(self, app):
        """Reset all the thread-local sessions generated."""
        def ViewContext_wsgi_setup_app(environ, start):
            for x in app(environ, start):
                yield x
            self._local.flash_messages = []
        return ViewContext_wsgi_setup_app
    
    # For reverse compatibility.
    wsgi_reset = wsgi_setup


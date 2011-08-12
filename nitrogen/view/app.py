"""nitrogen.view.environ"""


import os
import threading
import logging

import mako.lookup
from mako.exceptions import TopLevelLookupException as MakoLookupError
from mako.template import Template

from .defaults import context
from . import util

log = logging.getLogger(__name__)


class ViewAppMixin(object):
    """Environment for working with views/templates.
    
    Attributes:
        log -- A logger, customized by the name argument to the contructor.
        path -- A list of paths to check when rendering.
        globals -- Context defaults that apply to all threads.
        locals -- Context defaults that apply to only the current thread.
    
    """
    
    def setup_config(self):
        super(ViewAppMixin, self).setup_config()
        self.config.setdefault('template_path', [])
        self.config.setdefault('template_cache_dir', None)
    
    def __init__(self, *args, **kwargs):
        """Constructor.
        
        Parameters:
            name -- Used to specify which logger to use.
            path -- Initial list of paths to look for templates in.
        
        """
        
        # Need to set these up before calling the super so that other things
        # have access to them.
        self.view_globals = context.copy()
        self._view_locals = self.local()
        
        
        super(ViewAppMixin, self).__init__(*args, **kwargs)
        
        template_path = list(self.config.template_path)
        template_path.append(os.path.abspath(os.path.dirname(__file__) + '/../../templates'))
        
        self.lookup = mako.lookup.TemplateLookup(
            directories=template_path,
            module_directory=self.config.template_cache_dir,
            input_encoding='utf-8',
        )
        
        self.view_globals['url_for'] = lambda *args, **kwargs: self._local.request.url_for(*args, **kwargs)
        
    def export_to(self, map):
        super(ViewAppMixin, self).export_to(map)
        map.update(
            render=self.render,
            render_string=self.render_string,
            get_template=self.get_template,
        )
    
    @property
    def template_path(self):
        return self.lookup.directories
    
    @property
    def view_locals(self):
        """Return the underlying dict of the thread-local object."""
        return self._view_locals.__dict__
        
    def _prep_data(self, user_data):
        """Prepare user supplied data for use as a view context.
        
        Adds globals, locals, flash messages, etc.
        
        """
        data = {}
        data.update(self.view_globals)
        data.update(self.view_locals)
        data.update(user_data)
        return data
    
    def get_template(self, template):
        try:
            template = self.lookup.get_template(template)
            template.preprocessor = lambda x: util.inline_control_statements(util.whitespace_control(x))
        except MakoLookupError as e:
            return None
    
    def render(self, template, **data):
        """Find a template file and render it with the given keyword args.
        
        Searches on the current `self.path`.
        
        """
        if isinstance(template, basestring):
            template = self.lookup.get_template(template)
        data = self._prep_data(data)
        return template.render_unicode(**data)
    
    def render_string(self, template, **data):
        template = Template(template, lookup=self.lookup, **self.lookup.template_args)
        data = self._prep_data(data)
        return template.render_unicode(**data)
    
    
    


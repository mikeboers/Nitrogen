"""nitrogen.view.environ"""


import os
import threading
import logging

import mako.lookup
from mako.exceptions import TopLevelLookupException as MakoLookupError
from mako.template import Template

from .defaults import context


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
        self.view_globals['get_flash_messages'] = self.get_flash_messages
        self._warned_no_session = False
        
    def export_to(self, map):
        super(ViewAppMixin, self).export_to(map)
        map.update(
            render=self.render,
            get_template=self.get_template,
            flash=self.flash,
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
            return self.lookup.get_template(template)
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
    
    def _get_flash_messages(self):
        
        # Try to store them in the session (if it exists).
        session = self.request.session
        if session is not None:
            return session.get('_flash_messages', [])
        
        if not self._warned_no_session:
            log.warning('No session to store flash_messages in. Please setup session support.')
            self._warned_no_session = True
        
        # Store them locally if not, but they will not persist.
        return self._local.__dict__.get('flash_messages', [])
    
    def _set_flash_messages(self, messages):
        
        # Try to store them in the session (if it exists).
        session = self.request.session
        if session is not None:
            if not messages:
                session.pop('_flash_messages', None)
            else:
                session['_flash_messages'] = messages
            session.save()
            return
        
        self._local.__dict__['flash_messages'] = messages
        
    def get_flash_messages(self):
        messages = self._get_flash_messages()
        self._set_flash_messages([])
        return messages
    
    # Depricated    
    def add_flash_message(self, class_, message):
        self.flash(message, class_)
    
    def flash(self, message, class_=None):
        messages = self._get_flash_messages() + [(class_, message)]
        self._set_flash_messages(messages)
    
    


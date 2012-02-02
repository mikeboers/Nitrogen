"""nitrogen.view.environ"""
from __future__ import absolute_import

import os
import threading
import logging

import haml

from . import mako
from . import markdown

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
        self.config.setdefault('markdown_extensions', {})
    
    def __init__(self, *args, **kwargs):
        """Constructor.
        
        Parameters:
            name -- Used to specify which logger to use.
            path -- Initial list of paths to look for templates in.
        
        """
        
        # Need to set these up before calling the super so that other things
        # have access to them.
        self.view_globals = mako.defaults.copy()
        self._view_locals = self.local()
        
        
        super(ViewAppMixin, self).__init__(*args, **kwargs)
        
        template_path = list(self.config.template_path)
        template_path.append(os.path.abspath(os.path.dirname(__file__) + '/../../templates'))
        
        self.lookup = mako.TemplateLookup(
            directories=template_path,
            module_directory=self.config.template_cache_dir,
            input_encoding='utf-8',
            # Default in case no extensions match.
            preprocessor=[mako.whitespace_control, mako.inline_control_statements],
            # Provided by out extension to the TemplateLookup.
            preprocessors_by_ext=[
                ('.haml', [haml.preprocessor]),
            ],
            # The default unicode filter will be provided by our custom buffer
            # and context.
            default_filters=[],
        )
        
        self.view_globals.update(
            render=self.render,
            render_string=self.render_string,
            markdown=self.markdown,
            versioned_static=self.versioned_static,
            url_for= lambda *args, **kwargs: self._local.request.url_for(*args, **kwargs),
        )
        
    def export_to(self, map):
        super(ViewAppMixin, self).export_to(map)
        map.update(
            render=self.render,
            render_string=self.render_string,
            markdown=self.markdown,
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
    
    def render_template(self, template, **data):
        data = self._prep_data(data)
        
        # We must use our own custom buffer and context so that a default
        # unicode filter is applied AFTER all locally specified filters.
        context = mako.Context(mako.Buffer(), **data)
        context._outputting_as_unicode = True
        template.render_context(context, **data)
        return context._pop_buffer().getvalue()
    
    def render(self, template, **data):
        """Find a template file and render it with the given keyword args.
        
        Searches on the current `self.path`.
        
        """
        if isinstance(template, basestring):
            template = self.lookup.get_template(template)
        return self.render_template(template, **data)
    
    def render_string(self, template, **data):
        template = mako.Template(template, lookup=self.lookup, **self.lookup.template_args)
        return self.render_template(template, **data)
    
    def markdown(self, x, **custom_exts):
        exts = self.config.markdown_extensions.copy()
        exts.update(custom_exts)
        return markdown.markdown(x, **exts)

    def versioned_static(self, path):
        path = '/' + path.lstrip('/')
        mtime = self.static_router.get_mtime(path)
        if mtime:
            return '%s?v=%d' % (path, mtime)
        return path
        
    


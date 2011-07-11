import os
import functools
import logging
import threading

import beaker.session
import beaker.middleware
import werkzeug.utils

log = logging.getLogger(__name__)


class SessionAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(SessionAppMixin, self).__init__(*args, **kwargs)
        
        opts = {}
        for key in self.config:
            if key.startswith('session_'):
                opts[key[8:]] = self.config[key]
        if not opts:
            opts = dict(
                type='ext:database',
                url='sqlite://',
                key='session_id',
                secret=os.urandom(32),
            )
            
        opts['key'] = opts.get('key', 'session_id')
        
        if not self.config.private_key:
            log.warning('Session cookies will not be signed. Please set private_key.')
        secret = self.config.private_key
        secret = 'session-' + secret if secret else None
        opts['secret'] = secret
        
        self.register_middleware((self.FRAMEWORK_LAYER, 9), beaker.middleware.SessionMiddleware, None, opts)
        
        self.view_globals['get_flash_messages'] = self.get_flash_messages
        
    def export_to(self, map):
        super(SessionAppMixin, self).export_to(map)
        map.update(
            flash=self.flash,
        )
    
    def _get_flash_messages(self):

        # Try to store them in the session (if it exists).
        session = self.request.session
        if session is not None:
            return session.get('_flash_messages', [])

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

    def flash(self, message, class_=None):
        messages = self._get_flash_messages() + [(class_, message)]
        self._set_flash_messages(messages)
        
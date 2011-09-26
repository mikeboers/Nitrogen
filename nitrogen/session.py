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
        session = self.local_request().session
        if session is not None:
            messages = session.get('_flash_messages', [])
        else:
            messages = self._local.__dict__.get('flash_messages', [])
        # log.info('getting flash messages %r from %s' % (messages, 'session' if session is not None else 'local'))
        return messages

    def _set_flash_messages(self, messages):

        # Try to store them in the session (if it exists).
        session = self.local_request().session
        if session is not None:
            if not messages:
                session.pop('_flash_messages', None)
            else:
                session['_flash_messages'] = messages
            session.save()
            # log.info('set flash messages %r into session' % messages)
        else:
            self._local.__dict__['flash_messages'] = messages
            # log.info('set flash messages %r into local' % messages)

    def get_flash_messages(self):
        messages = self._get_flash_messages()
        self._set_flash_messages([])
        return messages

    def flash(self, message, class_=None):
        # log.info('flashing message %r' % message)
        messages = self._get_flash_messages() + [(class_, message)]
        self._set_flash_messages(messages)
        
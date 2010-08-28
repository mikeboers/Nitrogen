import os
import functools
import logging
import threading

import beaker.session
import beaker.middleware



log = logging.getLogger(__name__)


BeakerSignedCookie = beaker.session.SignedCookie
BeakerSession = beaker.session.Session
BeakerSessionObject = beaker.session.SessionObject
BeakerCookieSession = beaker.session.CookieSession
BeakerSessionMiddleware = beaker.middleware.SessionMiddleware


_local = threading.local()

def _start_patching():
    _local.depth = getattr(_local, 'depth', 0) + 1

def _stop_patching():
    _local.depth -= 1

class PatchMeta(type):
    
    def __new__(mcls, name, bases, ns):
        assert len(bases) == 1, 'Cannot patch more complex classes'
        ns['__patched_beaker_class__'] = bases[0]
        bases = (mcls.Patch, ) + bases
        return super(PatchMeta, mcls).__new__(mcls, name, bases, ns)

    class Patch(object):
        def __new__(cls, *args, **kwargs):
            if not getattr(_local, 'depth', 0):
                return cls.__patched_beaker_class__(*args, **kwargs)
            return super(PatchMeta.Patch, cls).__new__(cls, *args, **kwargs)

       
class SignedCookie(BeakerSignedCookie):
    __metaclass__ = PatchMeta

class Session(BeakerSession):
    __metaclass__ = PatchMeta

class CookieSession(BeakerCookieSession):
    __metaclass__ = PatchMeta
    
class SessionObject(BeakerSessionObject):
    __metaclass__ = PatchMeta

class SessionMiddleware(BeakerSessionMiddleware):
    __metaclass__ = PatchMeta
    



def patch_beaker_session_middleware(app):
    def _patch_beaker_middleware(environ, start):
        _start_patching()
        try:
            for x in app(environ, start):
                yield x
        finally:
            _stop_patching()
    return _patch_beaker_middleware

def make_patched_constructor(new_cls, old_cls):
    def _patched_constructor(*args, **kwargs):
        if getattr(_local, 'depth', 0):
            return new_cls(*args, **kwargs)
        return old_cls(*args, **kwargs)
    return _patched_constructor


beaker.session.SignedCookie      = SignedCookie
beaker.session.Session           = Session
beaker.session.CookieSession     = CookieSession
beaker.session.SessionObject     = SessionObject
beaker.session.SessionMiddleware = SessionMiddleware


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
        
        # self.register_middleware((self.FRAMEWORK_LAYER, 10), patch_beaker_session_middleware)
        self.register_middleware((self.FRAMEWORK_LAYER, 9), SessionMiddleware, None, opts)
        
        
        
        
        

import logging

import werkzeug as wz
import werkzeug.utils

from . import sign

log = logging.getLogger(__name__)


class _RequestMixin(object):
        
    @wz.utils.cached_property
    def raw_cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        return wz.utils.parse_cookie(self.environ, self.charset,
            cls=self.dict_storage_class)
                                
    @wz.utils.cached_property
    def cookies(self):
        """Read only access to the retrieved cookie values as dictionary."""
        raw = wz.utils.parse_cookie(self.environ, self.charset, cls=dict)
        if not self.app.config.private_key:
            return self.dict_storage_class(raw)
        ret = {}
        for key, raw_value in raw.iteritems():
            parts = raw_value.rsplit('?', 1)
            if len(parts) == 2:
                value, sig = parts
                sig = sign.decode_query(sig)
                if sign.verify(self.app.config.private_key, key + '=' + value, sig):
                    ret[key] = value
        return self.dict_storage_class(ret)


class _ResponseMixin(object):
    
    def set_raw_cookie(self, *args, **kwargs):
        super(_ResponseMixin, self).set_cookie(*args, **kwargs)
    
    def set_cookie(self, key, value='', max_age=None, *args, **kwargs):
        if self.app.config.private_key:
            sig = sign.sign(self.app.config.private_key, key + '=' + value, max_age=max_age)
            value = value + '?' + sign.encode_query(sig)
        self.set_raw_cookie(key, value, max_age, *args, **kwargs)


class CookieAppMixin(object):
    
    RequestMixin = _RequestMixin
    ResponseMixin = _ResponseMixin





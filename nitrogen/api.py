"""

"""

import json
import logging

from request import as_request


INTERNAL_ERROR = 'internal server error'

log = logging.getLogger(__name__)


class ApiError(Exception):
    pass

class ApiKeyError(KeyError, ApiError):
    pass

class ApiBase(dict):
    
    def log(self, logger=None, level=logging.INFO):
        (logger or log).log(level, '\n'.join([self.__class__.__name__] + [
            '    %s: %r' % x for x in sorted(self.items())]))
            
class ApiRequest(ApiBase):
    
    """WSGI API request helper class.
    
    """
    
    def __init__(self, request):
        dict.__init__(self, request.get)
        self.update(request.post)
        
        self.raw_request = request
        self.response = ApiResponse(self)
        
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError as e:
            raise ApiKeyError(key)
        
class ApiResponse(ApiBase):
    
    def __init__(self, request):
        self.request = request
        self.raw_response = request.raw_request.response
        self.started = False
        
        self['status'] = 'ok'
    
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type:
            self['status'] = 'error'
            if type is ApiKeyError:
                self['error'] = 'missing request argument %r' % value.args[0]
            elif type is ApiError:
                self['error'] = value.args[0]
            else:
                log.error('exception during api handling', exc_info=(type, value, traceback))
                self['error'] = INTERNAL_ERROR
        return True
        
    def start(self, code=None):
        if code is None:
            code = 200 if self.get('status') == 'ok' else 500
        self.raw_response.start(code, plain=True)
        self.started = True
    
    def encode(self, obj=None, indent=4, sort_keys=True):
        return json.dumps(obj or dict(self), indent=indent, sort_keys=sort_keys)
    
    def __iter__(self):
        
        status = self.get('status')
        error  = self.get('error')
        
        if status == 'error':
            if not error:
                log.error('error status with no error')
                error = INTERNAL_ERROR
        elif status != 'ok':
            log.error('bad status %r' % status)
            status = 'error'
            error = INTERNAL_ERROR
                
        if not self.started:
            self.start()
        
        if status == 'ok':
            return iter([self.encode()])
        
        # log.info(repr(status))
        # log.info(repr(error))
        
        log.warning('api error %r' % error)
        return iter([self.encode({
            'status': status,
            'error': error
        })])
        
        
def as_api(app):
    @as_request
    def inner(raw_request):
        request = ApiRequest(raw_request)
        with request.response:
            app(request, request.response)
        return request.response    
    return inner





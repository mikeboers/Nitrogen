"""

"""

import json
import logging

from request import Request, Response


INTERNAL_ERROR = 'internal server error'

log = logging.getLogger(__name__)


class ApiError(Exception):
    pass

class ApiKeyError(KeyError, ApiError):
    pass

class ApiBase(dict):
    
    def log_message(self):
        return '\n'.join([self.__class__.__name__] + [
            '    %s: %r' % x for x in sorted(self.items())])
        
    def log(self, logger=None, level=logging.INFO):
        (logger or log).log(level, self.log_message())
      
            
class ApiRequest(ApiBase):
    
    """WSGI API request helper class.
    
    """
    
    def __init__(self, request):
        if not isinstance(request, Request):
            request = Request(request)
        self.raw = request
        
        self.update(self.raw.get)
        self.update(self.raw.post)
        
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError as e:
            raise ApiKeyError(key)

   
class ApiResponse(ApiBase):
    
    def __init__(self, response=None, **kwargs):
        if response:
            if not isinstance(response, Response):
                response = Response(response)
        self.raw = response
        
        self.update(kwargs)
        
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
        # self.raw.content_type = 'application/json'    
        self.raw.content_type = 'text/plain'
        self.raw.start(code)
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
    def inner(environ, start):
        request = ApiRequest(environ)
        response = ApiResponse(start)
        with response:
            app(request, response)
        return response    
    return inner






import json
import logging
import datetime
import collections

from .request import Request, Response
from . import status


log = logging.getLogger(__name__)


class ApiError(Exception):
    pass


class ApiKeyError(KeyError, ApiError):
    pass
      

            
class ApiRequest(Request, collections.Mapping): 
    
    response_class = Response
    
    def log_message(self):
        return '\n'.join([self.__class__.__name__] + [
            '    %s: %r' % x for x in sorted(self.items())])
        
    def log(self, logger=None, level=logging.INFO):
        (logger or log).log(level, self.log_message())
    
    def __getitem__(self, key):
        try:
            return self.query[key]
        except KeyError:
            pass
        try:
            return self.form[key]
        except KeyError:
            pass
        raise ApiKeyError(key)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __iter__(self):
        visited = set()
        for x in self.query.keys():
            visited.add(x)
            yield x
        for x in self.form.keys():
            if x not in visited:
                yield x
    
    def __len__(self):
        return len(list(self))

    def json_default(self, value):
        if isinstance(value, datetime.date):
            ret = {}
            for key in 'year month day'.split():
                ret[key] = getattr(value, key)
            return ret
        raise TypeError()

    def encode(self, obj, indent=4, sort_keys=True):
        return json.dumps(obj, indent=indent, sort_keys=sort_keys, default=self.json_default)
    
    @classmethod
    def application(cls, func):
        def _application(*args):
            environ = args[-2]
            start   = args[-1]
            request = cls(environ)
            try:
                body = func(*(args[:-2] + (request, )))
                code = 200
            except ApiKeyError as e:
                body = 'missing argument %r' % e.args[0]
                code = 400
            except status.HTTPRedirection as e:
                raise # This will get handled down the stack.
            except status.HTTPException as e:
                body = e.detail or e.title
                code = e.code
            except Exception as e:
                log.exception('Error during Api.application.')
                body = 'internal server error'
                code = 500
            
            response = Response(request.encode(body), code)
            return response(environ, start)
            
        return _application
    


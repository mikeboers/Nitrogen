'''Generic API module.

Steps for general usage:
    1. Add error message keys and their format strings to the error_messages.
    2. Define api methods that take a single dict-like object (an ApiRequest)
        and perform some action, optionally modifying the request object.
        Raise ApiErrors if something is awry.
    3. Add method keys and their callbacks to the methods mapping.
    4. Call dispatch() with keywork arguments.
    
All request data is taken from keywork arguments to the dispatch method. The
method is looked up in the messages mapping. The method is called with the
request object as the single argument. Modifications to the request object are
returned as part of the result.

You can remove keys from the request object, but it is not considered good
practise.

'''

import re
import traceback
import inspect
import time

class Api(object):
    
    
    def __init__(self):
        self.methods = {}
        self.error_messages = {
            'api.internal.exception': 'Uncaught %(type)s: %(message)r',
            'api.internal.bad_error_key': 'No error key %(key)r found',
            'api.bad_method': 'No method named %(method)r found',
            'api.missing_parameter': 'Missing parameter %(parameter)r',
        }
        self.Error = self.Request = None
        self.__init_error_class()
        self.__init_request_class()
        
        # register class methods and error messages
        for k in dir(self):
            if k.startswith('method_'):
                self.methods[k[len('method_'):].replace('__', '.')] = \
                  getattr(self, k)
            elif k.startswith('ERROR_'):
                self.error_messages[k[6:].replace('__', '.')] = \
                  getattr(self, k)
    
    
    def dispatch(self, **kwargs):
        '''Process an API request -> dict.
        
        See module documentation for more info.
        
        '''
        
        req = self.Request(kwargs)
        
        # Decode it all to unicode
        for k in req:
            req[k] = req[k].decode('utf8')
        
        try:
            # get and verify the method exists
            method_key = req['method']
            callback = self.methods.get(method_key)
            if not callback:
                raise self.Error('api.bad_method', method = method_key)
            # make the call and assert success status
            callback(req)
            req['status'] = 'ok'
            req['method'] = method_key
        except self.Error, e:
            req.update(e.get_response())
        return dict(req)
    
    
    @staticmethod
    def method_api__signal(req):
        '''Does nothing.
        
        Useful to check if the communication channel to the API is clear, as
        this will return all values sent to it, in addition to a status of
        'ok'.
        
        '''
        
        return None
    
    
    def method_api__list(self, req):
        '''Returns a list of API methods.
        
        Return Keys:
            methods -- List of all API methods.
        
        '''
        
        req['methods'] = sorted(self.methods.keys())
    
    
    def method_api__inspect(self, req):
        '''Return documentation for a given method.
        
        Parameters:
            method_ -- The method to inspect.
        
        '''
        
        method = req['method_']
        callback = self.methods.get(method, None)
        if not callback:
            raise self.Error('api.inspect.bad_method', method=method)
        req['doc'] = inspect.cleandoc(callback.__doc__)
    
    ERROR_api__inspect__bad_method = \
      'No method named %(method)r to inspect.'
    
    
    def method_api__error(self, req):
        '''Raise an ApiError of type "api.test".'''
        raise self.Error('api.test')
    
    ERROR_api__test = 'This is just a test of the API method "api.error"'
    
    
    @staticmethod
    def method_api__exception(data):
        '''Raise a TestException.'''
        class TestException(Exception):
            pass
        raise TestException('This is just a test.')
    
    
    
    def __init_request_class(self):
        if self.Request:
            return
        api = self
        class ApiRequest(dict):
            
            '''API request object that is passed to API methods.'''
            
            def __getitem__(self, key):
                '''req['key'] -> FIRST value (if it exists).
                
                Raises an ApiError('api.missing_param') if the key is not
                found.
                
                '''
                
                if key not in self:
                    raise api.Error('api.missing_parameter', parameter = key)
                return dict.__getitem__(self, key)
        self.Request = ApiRequest
    
    def __init_error_class(self):
        if self.Error:
            return
        api = self
        class ApiError(Exception):
            '''Represents errors that are known to occour.'''
            
            def __init__(self, error_key = None, **kwargs):
                self.key = error_key 
                self.data = kwargs
                
                msg_pattern = api.error_messages.get(self.key, None)
                if not msg_pattern:
                    self.data = {
                        'data': self.data,
                        'key': self.key
                    }
                    self.key = 'api.internal.bad_error_key'
                    msg_pattern = api.error_messages.get(self.key)
                
                try:
                    message = msg_pattern % self.data
                except KeyError, e:
                    self.data = {
                        'data': data,
                        'error': self.key,
                        'key': str(e)
                    }
                    self.key = 'api.internal.bad_error_data'
                    message = \
                      'Error message format failure on key %r' % \
                      e.message
                Exception.__init__(self, message)
            
            def get_response(self):
                return {
                    'status': 'error',
                    'error': self.key,
                    'error_message': str(self),
                    'error_data': self.data
                }
        self.Error = ApiError






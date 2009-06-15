"""Generic API module.

Steps for general usage:
    1. Define api methods that take a single dict-like object (an ApiRequest)
        and perform some action, optionally modifying the request object.
        Raise ApiErrors if something is awry.
    2. Add method keys and their callbacks to the methods mapping.
    3. Call dispatch() with keyword arguments.
    
All request data is taken from keyword arguments to the dispatch method. The
method is looked up in the messages mapping. The method is called with the
request object as the single argument. Modifications to the request object are
returned as part of the result.

You can remove keys from the request object, but it is not considered good
practise.

Examples:

    >>> api = Api()
    >>> sorted(api.methods.keys())
    ['api.error', 'api.exception', 'api.inspect', 'api.list', 'api.signal']
    
    >>> api.dispatch(method='api.list')
    {'status': 'ok', 'method': u'api.list', 'methods': ['api.error', 'api.exception', 'api.inspect', 'api.list', 'api.signal']}
    
    >>> api.dispatch(method="api.signal")
    {'status': 'ok', 'method': u'api.signal'}
    
    # >>> api.dispatch(method="api.inspect", key="api.inspect")
    {'status': 'ok', 'doc': 'Return documentation for a given method.\n\nParameters:\n    key -- The method to inspect.', 'method': u'api.inspect', 'key': u'api.inspect'}
    
    >>> api.dispatch(method="api.error")
    {'status': 'error', 'method': u'api.error', 'error': 'Test error.'}
    
    >>> api.dispatch(method="api.exception")
    Traceback (most recent call last):
    ValueError: Test error.

"""

import re
import traceback
import inspect
import time

class ApiError(Exception):
    pass

class ApiRequest(dict):
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except:
            raise ApiError('Missing required argument %r.' % key)
        
class Api(object):
    
    def __init__(self):
        self.methods = {}
        
        # Register class methods which start with 'do_'.
        for key in dir(self):
            if key.startswith('do_'):
                method = getattr(self, key)
                self.methods[
                    key[len('do_'):].replace('__', '.')
                ] = method
    
    def register(self, method, name=None):
        """Decorator to register a method.
        
        >>> api = Api()
        >>> @api.register
        ... def test(res):
        ...     res['greeting'] = "Hello, World!"
        
        >>> api.dispatch(method='test')
        {'status': 'ok', 'method': u'test', 'greeting': 'Hello, World!'}
        
        """
        self.methods[name if name is not None else method.__name__.replace('__', '.')] = method
        return method
    
    def dispatch(self, **kwargs):
        
        req = ApiRequest(kwargs)
        
        # Put it all into unicode.
        for k in req:
            req[k] = unicode(req[k], 'utf8')
        
        try:
            # Get the method, and make sure it exists.
            method_key = req['method']
            callback = self.methods.get(method_key)
            if not callback:
                raise ApiError("Could not find method %r." % req['method'])
            # Make the call, and assert success status, and method value.
            callback(req)
            req['status'] = 'ok'
            req['method'] = method_key
        except ApiError as e:
            req.update(dict(
                status='error',
                error=str(e)
            ))
            if len(e.args) > 1:
                req['error_data'] = e.args[1]
            
        return dict(req)
    
    @staticmethod
    def do_api__signal(req):
        """Does nothing.
        
        Useful to check if the communication channel to the API is clear, as
        this will return all values sent to it, in addition to a status of
        'ok'.
        
        """
        pass
    
    def do_api__list(self, req):
        """Returns a list of API methods.
        
        Return Keys:
            methods -- List of all API methods.
        """
        req['methods'] = sorted(self.methods.keys())
    
    def do_api__inspect(self, req):
        """Return documentation for a given method.
        
        Parameters:
            key -- The method to inspect.
        
        """ 
        method = req['key']
        callback = self.methods.get(method, None)
        if not callback:
            raise ApiError('Could not find method %r.' % key)
        req['doc'] = inspect.cleandoc(callback.__doc__)
    
    def do_api__error(self, req):
        """Raise an ApiError."""
        raise ApiError('Test error.')
    
    @staticmethod
    def do_api__exception(req):
        """Raise a ValueError."""
        raise ValueError('Test error.')
    
    

if __name__ == '__main__':
    import doctest
    print 'Testing', __file__
    doctest.testmod()
    print 'Done.'




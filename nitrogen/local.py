"""Module with the old thread-local objects that were in the nitrogen.__init__

"""

raise ImportError('do not import %s' % __name__)

# Somewhere to hold threadsafe stuff.
# It should work just fine for cgi and fcgi.
# NOTE: I am assuming that this will work for the run_as_socket runner as well.
local = threading.local()

# Setup some dummy objects for testing.
local.environ = {}

class LocalProxy(object):
    """An object that proxies attribute and dict-like access to an object
    stored on the thread-local object under a given key.

    Params:
        key -- The name that the object is stored under on the thread-local
            object.
    
    """
    
    def __init__(self, key):
        object.__setattr__(self, '_local_key', key)
    
    def __repr__(self):
        return '<local.%s:%r>' % (self._local_key, local.__dict__.get(self._local_key))
    
    def __getattr__(self, key):
        return getattr(local.__dict__[self._local_key], key)
        
    def __setattr__(self, key, value):
        setattr(local.__dict__[self._local_key], key, value)
        
    def __delattr__(self, key):
        delattr(local.__dict__[self._local_key], key)
        
    def __getitem__(self, key):
        return local.__dict__[self._local_key][key]
        
    def __setitem__(self, key, value):
        local.__dict__[self._local_key][key] = value
        
    def __delitem__(self, key):
        del local.__dict__[self._local_key][key]
    
    def __contains__(self, key):
        return key in local.__dict__[self._local_key]


environ = LocalProxy('environ')
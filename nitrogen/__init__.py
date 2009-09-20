import threading
import logging
import sys
import os
import collections

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

def rawlog(*args):
    """Just in case I REALLY need to debug."""
    sys.stderr.write(' '.join(str(x) for x in args))
    sys.stderr.write('\n')
    sys.stderr.flush()


# Setup the path for the 3rd party packages in lib.
# Stuck on the front to overide anything in site-packages.
sys.path.insert(0, os.path.dirname(__file__) + '/lib')

# Somewhere to hold threadsafe stuff.
# It should work just fine for cgi and fcgi.
# NOTE: I am assuming that this will work for the run_as_socket runner as well.
local = threading.local()

def local_proxy(local_key):
    """Get an object that proxies to an object stored on the thread-local
    object.
    
    Params:
        local_key -- The name that the object is stored under on the thread-
            local object.
    
    Returns:
        An object which proxies attribute and dict-style access to the object
        stored on the thread-local object under the given key.        
    """
    
    class LocalProxy(object):
        def __getattr__(self, key):
            return getattr(local.__dict__[local_key], key)
        def __setattr__(self, key, value):
            setattr(local.__dict__[local_key], key, value)
        def __delattr__(self, key):
            delattr(local.__dict__[local_key], key)
        def __getitem__(self, key):
            return local.__dict__[local_key][key]
        def __setitem__(self, key, value):
            local.__dict__[local_key][key] = value
        def __delitem__(self, key):
            del local.__dict__[local_key][key]
        
    return LocalProxy()

environ = local_proxy('environ')

import configtools
import configtools.base

config = configtools.Config(configtools.extract_attributes(configtools.base))

# Try to get the nitrogenconfig module from the same level as nitrogen itself.
# This really is just a nasty hack...
config_module = None
try:
    config_name = __package__ + 'config'
    config_module = __import__(config_name, fromlist=['']) 
except ImportError as e:
    if str(e) != 'No module named %s' % config_name:
        raise
if config_module:
    config.update(configtools.extract_attributes(config_module))
else:
    print 'Could not find the nitrogenconfig.py file.'

    
server = configtools.get_server()

# Setup the logs.
import logs
root = logging.getLogger()
root.setLevel(config.log_level)
for handler in config.log_handlers:
    handler.setFormatter(logs.formatter)
    root.addHandler(handler)



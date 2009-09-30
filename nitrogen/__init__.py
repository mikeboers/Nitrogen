import threading
import logging
import sys
import os
import collections

logger = logging.getLogger(__name__)

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


class LocalProxy(object):
    """An object that proxies attribute and dict-like access to an object
    stored on the thread-local object under a given key.

    Params:
        key -- The name that the object is stored under on the thread-local
            object.
    
    """
    
    def __init__(self, key):
        object.__setattr__(self, '_local_key', key)
    
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


environ = LocalProxy('environ')

import configtools
import configtools.base


# Load the configuration.
config = configtools.Config(configtools.extract_attributes(configtools.base))
config_module = None
try:
    import nitrogenconfig as config_module
except ImportError:
    pass
if not config_module and __package__:
    try:
        # Try to get the nitrogenconfig module from the same level as nitrogen itself.
        # This really is just a nasty hack...
        config_name = __package__ + 'config'
        config_module = __import__(config_name, fromlist=[''])
    except ImportError:
        pass
if config_module:
    config.update(configtools.extract_attributes(config_module))
else:
    logger.warning('Could not find nitrogenconfig module.')

# Pull out the server.
server = config.server
if not server:
    raise ValueError('could not identify server')


# Setup the logs if it is requested.
if config.log_auto_setup:
    from . import logs
    logs.setup()


logger.debug('Imported nitrogen as %r.' % __name__)
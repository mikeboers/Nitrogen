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
    """Build a class that proxies a key on the thread-local object."""
    class LocalProxy(object):
        def __getattr__(self, key):
            return getattr(local.__dict__[local_key], key)
        def __setattr__(self, key, value):
            setattr(local.__dict__[local_key], key, value)
        def __delattr__(self, key):
            delattr(local.__dict__[local_key], key)
    return LocalProxy()

environ = local_proxy('environ')

import configtools
import configtools.base
config = configtools.Config(configtools.extract_locals(configtools.base))

# Try to get the nitrogenconfig module from the same level as nitrogen itself.
# This really is just a nasty hack...
if __package__:
    try:
        config_name = __package__ + 'config'
        config_module = __import__(config_name, fromlist=[''])
        config.update(configtools.extract_locals(config_module))
    except ImportError as e:
        config_module = None
        if str(e) == 'No module named %s' % config_name:
            # Could not find the module... Damn.
            pass
        else:
            raise

server = configtools.get_server()

# Setup the logs.
import logs
root = logging.getLogger()
root.setLevel(config.log_level)
for handler in config.log_handlers:
    handler.setFormatter(logs.formatter)
    root.addHandler(handler)



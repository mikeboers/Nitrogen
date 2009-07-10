import threading
import logging
import sys
import os

# Setup path for local testing.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])
    __package__ = 'nitrogen'
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

from configtools import AttrDict, extract_locals, get_server
import configtools.base
config = AttrDict(extract_locals(configtools.base))

# Try to get the nitrogenconfig module from the same level as nitrogen itself.
# This really is just a nasty hack...
if __package__:
    try:
        config_name = __package__ + 'config'
        config_module = __import__(config_name, fromlist=[''])
        config.update(extract_locals(config_module))
    except ImportError as e:
        config_module = None
        if str(e) == 'No module named %s' % config_name:
            # Could not find the module... Damn.
            pass
        else:
            raise

server = get_server()

# Setup the logs.
import logs
root = logging.getLogger()
root.setLevel(config.log_level)
for handler in config.log_handlers:
    handler.setFormatter(logs.formatter)
    root.addHandler(handler)




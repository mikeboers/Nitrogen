import threading

# Setup path for local testing.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

from configtools import extract_locals, get_server

# Setup the lib
import lib

# Somewhere to hold threadsafe stuff.
# It should work just fine for cgi and fcgi.
# NOTE: I am assuming that this will work for the run_as_socket runner as well.
local = threading.local()

class ConfigDict(dict):
    def __getattr__(self, key):
        return self.get(key)

config = ConfigDict()
server = None

def setup(config_module):
    global server
    assert not server, 'You can only setup nitrogen once!'
    
    config.update(extract_locals(config_module))
    server = config.server = get_server()
    for (k, v) in config.server.items():
        if config.get(k) is None:
            config[k] = v

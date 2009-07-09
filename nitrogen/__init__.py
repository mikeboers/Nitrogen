import threading
import logging
import sys

# Setup path for local testing.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

from configtools import extract_locals, get_server

# Setup the lib
import lib
lib.setup()

# Somewhere to hold threadsafe stuff.
# It should work just fine for cgi and fcgi.
# NOTE: I am assuming that this will work for the run_as_socket runner as well.
local = threading.local()

class ConfigDict(dict):
    def __getattr__(self, key):
        return self.get(key)

config = ConfigDict()
server = None

def log(*args):
    sys.stderr.write(' '.join(str(x) for x in args))
    sys.stderr.write('\n')
    sys.stderr.flush()

if __package__:
    log('package:', __package__)
    try:
        config_module = __import__(__name__ + 'config', level=2)
        log(config_module)
    except ImportError as e:
        log('Could not find the config module.')
        log(e)
    
def setup(config_module):
    global server
    assert not server, 'You can only setup nitrogen once!'
    
    config.update(extract_locals(config_module))
    server = config.server = get_server()
    for (k, v) in config.server.items():
        if config.get(k) is None:
            config[k] = v

def debug():
    import pdb
    import socket
    import sys
    import io
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('localhost', 9000))
    stdin = io.open(sock.fileno(), 'rb')
    stdout = io.open(sock.fileno(), 'wb')
    pdb.Pdb(stdin=stdin, stdout=stdout).set_trace()
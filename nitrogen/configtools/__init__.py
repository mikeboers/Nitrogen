import collections
import os

import base

_servers = []

class Server(collections.Mapping):
    def __init__(self, **kwargs):
        self._data = kwargs
    def __getitem__(self, key):
        return self._data[key]
    def __iter__(self):
        return iter(self._data)
    def __len__(self):
        return len(self._data)
    def __getattr__(self, key):
        return self._data.get(key)
    def __repr__(self):
        return 'Server(%s)' % ', '.join('%s=%r' % x for x in sorted(self._data.items()))

def register_server(**kwargs):
    server = Server(**kwargs)
    _servers.append(server)
    return server

def get_server():
    path = os.path.abspath(__file__)
    possible_servers = [server for server in _servers if path.startswith(server.www_root)]
    if not possible_servers:
        raise ValueError('Could not identify the server we are on.', os.path.abspath(__file__))
    return possible_servers[0]

def extract_locals(module, all=False):
    return dict((k, getattr(module, k)) for k in dir(module) if all or not k.startswith('_'))

class AttrDict(dict):
    def __getattr__(self, key):
        return self.get(key)
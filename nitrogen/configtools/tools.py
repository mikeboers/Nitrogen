import collections
import os
import re

servers = []

from .. import environ

class Server(object):
    
    def __init__(self, **kwargs):
        self._data = kwargs
    def __getattr__(self, key):
        return self._data.get(key)
    
    @property
    def admin_domain(self):
        return 'admin.' + self.domain
    
    @property
    def cookie_domain(self):
        return '.' + self.domain
    
def register_server(**kwargs):
    server = Server(**kwargs)
    servers.append(server)
    return server

def get_server():
    path = os.path.abspath(__file__)
    possibleservers = [server for server in servers if path.startswith(server.www_root)]
    if not possibleservers:
        raise ValueError('Could not identify server.')
    return possibleservers[0]
    
def get_server_by(**kwargs):
    """Find a server from those which are registered. Takes a single keyword
    argument specifying the attribute to match on.
    """
    
    if len(kwargs) != 1:
        raise ValueError('Can only search with one parameter.')

    key, value in kwargs.items()[0]
    possibleservers = [x for x in servers if getattr(x, key) == value]
    
    return possibleservers[0] if possibleservers else None

def extract_locals(module, all=False):
    return dict((k, getattr(module, k)) for k in dir(module) if all or not k.startswith('_'))

class Config(dict):
    """An object to represent configuration of the system. It supports both
    dict-like access and property access.
    
    Properties will return None if they don't exist. Also, values which are
    property objects will have their getter called if accessed as a property.
    """
    def __getattr__(self, key):
        v = self.get(key)
        if isinstance(v, property):
            return v.fget()
        return v
    def __setattr__(self, key, value):
        self[key] = value
    def __delattr__(self, key):
        try:
            del self[key]
        except:
            pass
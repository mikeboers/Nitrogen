import collections
import os
import re

servers = []

# Import the environ for the nitrogenconfig.py to use.
from .. import environ

class _Server(object):
    """Read-only server specification."""
    
    def __init__(self, **kwargs):
        self._data = kwargs
    def __getattr__(self, key):
        return self._data.get(key)
    def get(self, *args, **kwargs):
        return self._data.get(*arg, **kwargs)
    def __getitem__(self, key):
        return self._data[key]
    
    @property
    def admin_domain(self):
        if 'admin_domain' in self._data:
            return self._data['admin_domain']
        return 'admin.' + self.domain
    
    @property
    def cookie_domain(self):
        if 'cookie_domain' in self._data:
            return self._data['cookie_domain']
        return '.' + self.domain
    
def register_server(**kwargs):
    """Register a set of keyword arguments as a possible server that we are on."""
    server = _Server(**kwargs)
    servers.append(server)
    return server

def get_server():
    """Attempts to return the registered server that is currently being run.
    
    Does so by finding all the servers whose www_root is around this file. If
    there is more than one, it returns the most specific.
    
    """
    path = os.path.abspath(__file__)
    possibleservers = [server for server in servers if path.startswith(server.www_root)]
    if not possibleservers:
        raise ValueError('Could not identify server.')
    possibleservers.sort(key=lambda x: -len(x.www_root))
    return possibleservers[0]
    
def get_server_by(**kwargs):
    """Find a server from those which are registered. Takes a single keyword
    argument specifying the attribute to match on.
    """
    
    if len(kwargs) != 1:
        raise ValueError('Can only search with one parameter.')

    key, value = kwargs.items()[0]
    possibleservers = [x for x in servers if getattr(x, key) == value]
    
    return possibleservers[0] if possibleservers else None

def extract_attributes(obj, all=False):
    """Builds a dictionary of all attributes on a given object.
    
    Useful for modules which do not internally store everything in a __dict__
    attribute.
    
    Params:
        obj -- The object to pull attributes from.
        all -- Should we pull everything, or treat '_' prefixes as private?
    
    Returns:
        A dict.
    """
    return dict((k, getattr(obj, k)) for k in dir(obj) if all or not k.startswith('_'))

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
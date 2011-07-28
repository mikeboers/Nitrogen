import collections
import os
import re
import json


class ConfigFile(collections.Mapping):
    
    def __init__(self, path, defaults=()):
        self.path = path
        self.defaults = defaults
        self.data = dict(defaults)
        self._exists = False
        
        try:
            self.load()
        except IOError:
            pass
    
    @property
    def exists(self):
        return self._exists
    
    def __getitem__(self, name):
        return self.data[name]
    
    def __iter__(self):
        return iter(self.data)
    
    def __len__(self):
        return len(self.data)
    
    def load(self):
        with open(self.path, 'rb') as f:
            self.data.update(json.load(f))
            self._exists = True
    
    def save(self):
        with open(self.path, 'wb') as f:
            json.dump(self.data, f, indent=4)
    
    def interactive_build(self):
        if not os.isatty(0):
            raise RuntimeError('not a TTY')
        
        data = self.data

        for name, default in self.defaults:
            current = data.get(name, default)
            if isinstance(default, bool):
                while True:
                    x = raw_input('%s (%s): ' % (name, '[y] or n' if current else 'y or [n]')).strip().lower()
                    x = {'y': True, 'n': False, '': current}.get(x)
                    if x is not None:
                        data[name] = x
                        break
                    else:
                        print 'Invalid response.'
            else:
                data[name] = raw_input('%s [%s]: ' % (name, current)).strip() or current
    
    def export_to(self, obj):
        obj.update(self.data)
    
    

class Server(dict):
    
    def __init__(self, name, **kwargs):
        self.__name = name
        dict.__init__(self, name=name, **kwargs)
    
    def __hash__(self):
        return hash(self.__name)
    
    @property
    def name(self):
        return self.__name
    
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        del self[key]

class ServerList(object):
    server_class = Server
    
    def __init__(self):
        self.list = []

    def register(self, **kwargs):
        """Register a set of keyword arguments as a possible server that we are
        on.
        """
        server = self.server_class(**kwargs)
        self.list.append(server)
        return server

    def find_by(self, **kwargs):
        """Find a server from those which are registered. Takes a single keyword
        argument specifying the attribute to match on.
        """
        
        matches = []
        for server in self.list:
            for k, v in kwargs.iteritems():
                if k not in server or server[k] != v:
                    break
            else:
                matches.append(server)
        return matches
            
    def find_first_by(self, **kwargs):
        """Find a server from those which are registered. Takes a single keyword
        argument specifying the attribute to match on.
        """
        
        matches = self.find_by(**kwargs)
        return matches[0] if matches else None





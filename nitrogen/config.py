import collections
import os
import re
import json


class Config(dict):
    
    def __getattribute__(self, name):
        try:
            return self[name]
        except KeyError:
            pass
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            pass
    
    def setdefaults(self, **kwargs):
        results = {}
        for name, default in kwargs.iteritems():
            results[name] = self.setdefault(name, default)
        return results
    
    def filter_prefix(self, prefix):
        filtered = {}
        for key, value in self.iteritems():
            if key.startswith(prefix):
                filtered[key[len(prefix):]] = value
        return filtered


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


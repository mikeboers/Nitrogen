import collections
import os
import re


class Server(dict):
    
    def __init__(self, name, **kwargs):
        self.__name = name
        dict.__init__(self, **kwargs)
    
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



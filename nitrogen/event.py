'''Very basic Observer pattern.'''

import werkzeug as wz
import werkzeug.utils


class Event(object):
    
    def __init__(self):
        self.listeners = []
    
    def listen(self, func):
        self.listeners.append(func)
    
    def remove(self, func):
        self.listeners.remove(func)
    
    def itertrigger(self, *args, **kwargs):
        for func in self.listeners:
            yield func(*args, **kwargs)
            
    def trigger(self, *args, **kwargs):
        return list(self.itertrigger(*args, **kwargs))


def instance_event(name):
    return wz.utils.cached_property(lambda x: Event(), name=name)
    
    

        
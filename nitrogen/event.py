'''Very basic Observer pattern.'''


from werkzeug.utils import cached_property

class Event(object):
    
    def __init__(self):
        self.listeners = []
    
    def listen(self, func):
        self.listeners.append(func)
    
    def remove(self, func):
        self.listeners.remove(func)
    
    def itrigger(self, *args, **kwargs):
        for func in self.listeners:
            yield func(*args, **kwargs)
            
    def trigger(self, *args, **kwargs):
        return list(self.itrigger(*args, **kwargs))


def instance_event(name):
    return cached_property(lambda x: Event(), name=name)
    
    

        
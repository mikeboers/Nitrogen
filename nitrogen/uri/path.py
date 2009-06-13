"""Module for query.Path object."""

from transcode import *

class Path(list):
    
    def __init__(self, input=None):
        self.relative = False
        if not input:
            return
        if isinstance(input, basestring):
            if input and input[0] == '/':
                self.absolute = True
                input = input[1:]
            self.extend(decode(x) for x in input.split('/'))
        else:
            self.extend(input)
    
    @property
    def absolute(self):
        return not self.relative
    
    @absolute.setter
    def absolute(self, value):
        self.relative = not value
    
    def __str__(self):
        return ('/' if self.absolute else '') + '/'.join(encode(x, SUB_DELIMS + '@:') for x in self)
    
    def __repr__(self):
        return '<uri.Path:%s>' % list.__repr__(self)
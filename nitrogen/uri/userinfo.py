"""Module for query.Userinfo object."""

from transcode import *

class Userinfo(list):
    
    def __init__(self, input=None):
        if not input:
            return
        if isinstance(input, basestring):
            self.extend(decode(x) for x in input.split(':'))
        else:
            self.extend(input)

    def __str__(self):
        return ':'.join(encode(x, SUB_DELIMS) for x in self)
    
    def __repr__(self):
        return '<uri.Userinfo:%s>' % list.__repr__(self)
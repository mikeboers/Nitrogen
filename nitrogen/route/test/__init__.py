
from pprint import pprint

from webtest import TestApp as WebTester

from .. import *
from ..base import *





class EchoApp(object):
    
    """Simple app for route testing.
    
    Just echos out a string given at construnction time.
    
    """
    
    def __init__(self, output=None, start=True):
        self.start = start
        self.output = output
    
    def __call__(self, environ, start):
        if self.start:
            start('200 OK', [('Content-Type', 'text/plain')])
        return [str(self.output)]
    
    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.output)
        
        
        
        
      
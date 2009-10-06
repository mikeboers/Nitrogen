
# Setup path for local evaluation.
# When copying to another file, just change the parameter to be accurate.
if __name__ == '__main__':
    def __local_eval_fix(package):
        global __package__
        import sys
        __package__ = package
        sys.path.insert(0, '/'.join(['..'] * (1 + package.count('.'))))
        __import__(__package__)
    __local_eval_fix('nitrogen.uri')

from ..status import HttpNotFound

class Chain(list):
    
    def __init__(self, *args):
        self.extend(args)
    
    def __call__(self, environ, start):
        for router in self:
            try:
                return router(environ, start)
            except HttpNotFound:
                pass
        raise HttpNotFound()
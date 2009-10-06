
# Setup path for local evaluation.
# When copying to another file, just change the parameter to be accurate.
if __name__ == '__main__':
    def __local_eval_fix(package):
        global __package__
        import sys
        __package__ = package
        sys.path.insert(0, '/'.join(['..'] * (1 + package.count('.'))))
        __import__(__package__)
    __local_eval_fix('nitrogen.route')


from tools import *
from filerouter import FileRouter
from rerouter import ReRouter
from selfrouter import SelfRouter



if __name__ == '__main__':
    from .. import test
    test.run()
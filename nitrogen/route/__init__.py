
# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen.route'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)


from routes import Mapper
from routes.middleware import RoutesMiddleware as router

from tools import *
from filerouter import FileRouter
from rerouter import ReRouter
from selfrouter import SelfRouter



if __name__ == '__main__':
    from .. import test
    test.run()
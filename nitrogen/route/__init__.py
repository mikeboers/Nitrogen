# Setup path for local testing.
if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__[:__file__.rfind('/nitrogen')])

from nitrogen.route.tools import *
from nitrogen.route.filerouter import FileRouter
from nitrogen.route.rerouter import ReRouter
from nitrogen.route.selfrouter import SelfRouter
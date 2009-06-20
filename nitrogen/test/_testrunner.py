from __init__ import *

import random

class TestTestRunner(unittest.TestCase):
    """This module is for testing the test runner.
    
    Doctest:
        >>> True
        True
        >>> False
        False
    """
    def test_pass(self):
        self.assert_(True)

def setup_module():
    print 'setup_module()'

def teardown_module():
    print 'teardown_module()'

def setup():
    print 'setup()'

def teardown():
    print 'teardown()'

def wrap(test):
    test.setup = setup
    test.teardown = teardown
    return test

@wrap
def test_nose():
    """
    >>> "Hello world!"
    'Hello world!'
    """
    print 'test_nose()'
    assert True, "Nose does not work."

if __name__ == '__main__':
    run()
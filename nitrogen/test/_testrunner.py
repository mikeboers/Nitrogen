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

def test_nose():
    assert True, "Nose does not work."

if __name__ == '__main__':
    run()
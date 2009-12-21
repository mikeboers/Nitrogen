"""

>>> 1
1


"""

import unittest
import wsgiref.util
from pprint import pprint
import re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

__all__ = 'unittest run'.split()


def run():
    """Find all the tests in the __main__ module, and run them.
    
    Looks for nose tests, unittest.TestCase tests, and doc tests.
    """
    
    import os
    import sys
    import doctest
    import logging
    
    logging.getLogger('nose').setLevel(1000)
    root = logging.getLogger()
    root.setLevel(0)
    stderr = logging.StreamHandler()
    root.addHandler(stderr)
    stderr.setFormatter(logging.Formatter("%(name)s.%(levelname)s - %(message)s"))
    sys.path.append(os.path.abspath(__file__ + '/../../lib'))
    import nose.loader
    
    # Grab the main module/
    m = sys.modules.get('__main__')
    
    # Setup test infrastructure.
    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()
    
    # Pull in doctests from module.
    try:
        doc_suite = doctest.DocTestSuite(m)
        suite.addTest(doc_suite)
        doc_count = doc_suite.countTestCases()
        if doc_count:
            print "Found %d doc test%s." % (doc_count, 's' if doc_count > 1 else '')
    except:
        doc_suite = None
    
    # Add the nose (and unittest) tests.
    nose_loader = nose.loader.TestLoader()
    nose_suite = nose_loader.loadTestsFromModule(m)
    nose_count = len(list(nose_suite._get_tests()))
    if nose_count:
        print "Found %d nose/unittest test%s." % (nose_count, 's' if nose_count > 1 else '')
        suite.addTest(nose_suite)    
    
    # Nessesary for Windows.
    sys.stderr.flush()
    sys.stdout.flush()
    
    # GO!
    test_count = suite.countTestCases()
    if test_count:
        print '-' * 70
        print 'Running %s tests...' % test_count
        print
        runner.run(suite)
    else:
        print "Could not find any tests."

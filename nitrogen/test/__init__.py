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
    
    # Try to find coresponding test file.
    test_path = m.__file__[:-3] + '.doctest'
    if os.path.exists(test_path):
        try:
            suite.addTest(doctest.DocFileSuite(test_path, module_relative=False, encoding='utf8'))
            print "Found doc test file."
        except:
            pass
    
    # Add the nose (and unittest) tests.
    nose_loader = nose.loader.TestLoader()
    nose_suite = nose_loader.loadTestsFromModule(m)
    nose_count = len(list(nose_suite._get_tests()))
    if nose_count:
        print "Found %d nose/unittest test%s." % (nose_count, 's' if nose_count > 1 else '')
        suite.addTest(nose_suite)    
    
    # GO!
    test_count = suite.countTestCases()
    if test_count:
        print '-' * 70
        print 'RUNNING %s TESTS' % test_count
        print
        runner.run(suite)
    else:
        print "COULD NOT FIND ANY TESTS!"
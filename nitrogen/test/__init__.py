import unittest
TestCase = unittest.TestCase

def run():
    import os
    import sys
    import doctest
    
    sys.path.append('../lib')
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
        print "Found %d doc tests." % doc_suite.countTestCases()
    except:
        doc_suite = None
    
    # Try to find coresponding test file.
    test_path = m.__file__[:-3] + '.test'
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
        print "Found %d nose/unittest tests." % nose_count
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
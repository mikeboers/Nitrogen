import unittest
TestCase = unittest.TestCase

def run():
    import sys
    sys.path.append('../lib')


    runner = unittest.TextTestRunner()
    suite = unittest.TestSuite()

    import doctest
    try:
        suite.addTest(doctest.DocTestSuite('__main__'))
    except:
        doc_suite = None

    import nose.loader
    nose_loader = nose.loader.TestLoader()
    suite.addTest(nose_loader.loadTestsFromName('__main__'))    

    runner.run(suite)
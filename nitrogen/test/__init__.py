import unittest
import wsgiref.util
from pprint import pprint
import re

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

__all__ = 'unittest WSGIServer run'.split()



def create_wsgi_environ(input=''):
    """Returns a dict for use as a wsgi environ.
    
    This was constructed by looking at the return of 
    wsgiref.util.setup_testing_defaults.
    
    """
    return {
        'HTTP_HOST': 'test.example.com', # This was 127.0.0.1
        'PATH_INFO': '/',
        'REQUEST_METHOD': 'GET',
        'SCRIPT_NAME': '',
        'SERVER_NAME': '127.0.0.1',
        'SERVER_PORT': '80',
        'SERVER_PROTOCOL': 'HTTP/1.0',
        'wsgi.errors': StringIO(),
        'wsgi.input': StringIO(input),
        'wsgi.multiprocess': 0,
        'wsgi.multithread': 0,
        'wsgi.run_once': 0,
        'wsgi.url_scheme': 'http',
        'wsgi.version': (1, 0)
    }

class WSGIServer(object):
    """Basic WSGI testing server."""
    
    def __init__(self, app=None, input=None):
        self.app = app
        self.input = input
        
    def run(self, app=None, input=None, **kwargs):
        self.environ = create_wsgi_environ(input or self.input or '')
        self.environ.update(kwargs)
        self.started = False
        self.output = []
        for x in (app or self.app)(self.environ, self._start):
            if not self.started:
                raise ValueError("Recieved output before start.")
            if not isinstance(x, str):
                raise TypeError("Iterator returned non-str.")
            self.output.append(x)
        if not self.started:
            raise ValueError("No content at all.")
        return self.status, self.headers, ''.join(self.output)
        
    def _start(self, status, headers):
        if self.started:
            raise ValueError("App has already started.")
        self.started = True
        if not isinstance(status, str):
            raise TypeError("Status must be a string.")
        if not re.match(r'\d{3} .+', status):
            raise ValueError('Status does not appear to be properly formatted.', self.status)
        self.status = status
        if not isinstance(headers, list):
            raise TypeError("Headers must be a list.")
        for x in headers:
            x = tuple(x)
            if len(x) != 2:
                raise ValueError("Header is not length 2.", x)
        self.headers = headers
    
    def __iter__(self):
        return iter(self.output)

def run():
    """Find all the tests in the __main__ module, and run them.
    
    Looks for nose tests, unittest.TestCase tests, and doc tests.
    """
    
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
        doc_count = doc_suite.countTestCases()
        if doc_count:
            print "Found %d doc test%s." % (doc_count, 's' if doc_count > 1 else '')
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
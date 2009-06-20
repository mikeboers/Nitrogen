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
    pass
    #print 'setup_module()'

def teardown_module():
    pass
    #print 'teardown_module()'

def setup():
    pass
    #print 'setup()'

def teardown():
    pass
    #print 'teardown()'

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
    #print 'test_nose()'
    assert True, "Nose does not work."



def basic_app(env, start):
    start('200 OK', [])
    yield 'Hiya!'

def test_app():
    status, headers, output = WSGIServer(basic_app).run()
    assert status == '200 OK'
    assert headers == []
    assert output == 'Hiya!', "Output was not as expected."
    
def env_app(env, start):
    start('200 OK', [])
    for x in sorted(env.items()):
        yield '%s: %r\n' % x
    
def test_env_app():
    status, headers, output = WSGIServer(env_app).run()
    assert re.match(r"""HTTP_HOST: 'test.example.com'
PATH_INFO: '/'
REQUEST_METHOD: 'GET'
SCRIPT_NAME: ''
SERVER_NAME: '127.0.0.1'
SERVER_PORT: '80'
SERVER_PROTOCOL: 'HTTP/1.0'
wsgi.errors: <cStringIO.StringO object at 0x\w+>
wsgi.input: <cStringIO.StringI object at 0x\w+>
wsgi.multiprocess: 0
wsgi.multithread: 0
wsgi.run_once: 0
wsgi.url_scheme: 'http'
wsgi.version: \(1, 0\)
""", output)
    
    
    
    
    
    
    
    
    
    

if __name__ == '__main__':
    run()
from __init__ import *

import random
import re

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




def test_basic_app():
    from webtest import TestApp

    def app(env, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'Hiya!'
    app = TestApp(app)

    res = app.get('/')
    assert res.body == 'Hiya!', "Output is wrong."


def test_env_app():
    from webtest import TestApp
    def app(env, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        for x in sorted(env.items()):
            yield '%s: %r\n' % x
    app = TestApp(app)

    res = app.get('/')
    assert re.match(r"""HTTP_HOST: 'localhost:80'
PATH_INFO: '/'
QUERY_STRING: ''
REQUEST_METHOD: 'GET'
SCRIPT_NAME: ''
SERVER_NAME: 'localhost'
SERVER_PORT: '80'
SERVER_PROTOCOL: 'HTTP/1.0'
paste.testing: True
paste.testing_variables: {}
paste.throw_errors: True
wsgi.errors: <webtest.lint.ErrorWrapper object at 0x\w+>
wsgi.input: <webtest.lint.InputWrapper object at 0x\w+>
wsgi.multiprocess: False
wsgi.multithread: False
wsgi.run_once: False
wsgi.url_scheme: 'http'
wsgi.version: \(1, 0\)
""", res.body)











if __name__ == '__main__':
    run()

import unittest

import werkzeug as wz
import werkzeug.test
import werkzeug.wrappers

from . import sign


PRIVATE_KEY = '0123456789abcdef'

app_config = dict(
    private_key=PRIVATE_KEY,
    sqlalchemy_url='sqlite://',
)


class TestCase(unittest.TestCase):
    pass


class Client(wz.test.Client):
    pass
    


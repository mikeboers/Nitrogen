
import unittest
from pprint import pprint

from webtest import TestApp as WebTester

from .tools import Router, TestApp, RouteChunk, Unroutable, GenerationError
from ..http.status import HttpNotFound

class PrefixRouter(Router, dict):
    
    def __init__(self, data_key='prefix'):
        self.data_key = data_key
    
    def __repr__(self):
        return '<%s.%s:%r>' % (__name__, self.__class__.__name__,
            sorted(self.keys()))
    
    def register(self, prefix, child=None):
        prefix = str(prefix)
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        if child is not None:
            dict.__setitem__(self, prefix, child)
            return child
        def PrefixRouter_register(child):
            self.register(prefix, child)
        return PrefixRouter_register
    
    __setitem__ = register
    
    def route_step(self, path):
        for prefix, child in self.iteritems():
            if path == prefix or path.startswith(prefix) and path[len(prefix)] == '/':
                return child, path[len(prefix):], {self.data_key:prefix}
    
    def generate_step(self, data):
        prefix = data.get(self.data_key)
        if prefix is None:
            return
        if not prefix.startswith('/'):
            prefix = '/' + prefix
        if prefix in self:
            return prefix, self[prefix]



    

class TestCase(unittest.TestCase):
    
    def test_main(self):
    
        app1 = TestApp('one')
        app2 = TestApp('two')
        app3 = TestApp('three')
    
        router = PrefixRouter('first')
        a = PrefixRouter('second')
        b = PrefixRouter('second')

        router.register('/a', a)
        router.register('b', b)
    
        a.register('/1', app1)
        a.register('/2', app2)
        b.register('2', app2)
        b.register('3', app3)
    
        # print router
        # print a
        # print b
        
        route, child, path = router.route('/a/1')
        # pprint(route)
        self.assertEqual(route, [
            RouteChunk('/a/1'),
            RouteChunk('/1', router, dict(first='/a')),
            RouteChunk('', a, dict(second='/1')),
        ])
        self.assertEqual(child, app1)
        self.assertEqual(path, '')
        
        route, child, path = router.route('/b/2/more')
        self.assertEqual(route, [
            RouteChunk('/b/2/more'),
            RouteChunk('/2/more', router, dict(first='/b')),
            RouteChunk('/more', b, dict(second='/2')),
        ])
        self.assertEqual(child, app2)
        self.assertEqual(path, '/more')
        
        try:
            router.route('/a/extra')
            self.fail()
        except Unroutable as e:
            self.assertEqual(e.args, ([
                RouteChunk('/a/extra'),
                RouteChunk('/extra', router, dict(first='/a'))
            ], a, '/extra'))
        
        app = WebTester(router)
        
        res = app.get('/a/1')
        self.assertEqual(res.body, 'one')
        res = app.get('/b/2')
        self.assertEqual(res.body, 'two')
        try:
            res = app.get('/b/4')
            self.fail()
        except HttpNotFound as e:
            pass
        
        
        self.assertEquals('/a/1', router.url_for(**dict(first='a', second='1')))
        self.assertEquals('/b/2', router.url_for(**dict(first='b', second='2')))
        try:
            router.url_for(**dict(first='a'))
        except GenerationError as e:
            self.assertEquals(e.args, ('/a', a, dict(first='a')))
        
        route, child, path = router.route('/a/1')
        
        self.assertEquals('/a/2', route.url_for(**dict(second='2')))
        self.assertEquals('/a/1', route.url_for(**dict(first='a')))
        self.assertEquals('/b/3', route.url_for(**dict(first='b', second='3')))
        try:
            x = route.url_for(**dict(first='b'))
            self.fail(x)
        except GenerationError as e:
            self.assertEquals(e.args, ('/b', b, dict(first='b')))
            




if __name__ == '__main__':
    from .. import test
    test.run()
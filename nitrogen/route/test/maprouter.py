
import unittest

from ...http.status import HTTPNotFound
from ..core import RouteHistoryChunk, RoutingError, GenerationError
from ..maprouter import *
from . import EchoApp

class TestCase(unittest.TestCase):
    
    def test_main(self):
        
        
        app1 = EchoApp('one')
        app2 = EchoApp('two')
        app3 = EchoApp('three')
    
        router = MapRouter('first')
        a = MapRouter('second')
        b = MapRouter('second')

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
            RouteHistoryChunk('/a/1', None, None),
            RouteHistoryChunk('/1', router, dict(first='/a')),
            RouteHistoryChunk('', a, dict(second='/1')),
        ])
        self.assertEqual(child, app1)
        self.assertEqual(path, '')
        
        route, child, path = router.route('/b/2/more')
        self.assertEqual(route, [
            RouteHistoryChunk('/b/2/more', None, None),
            RouteHistoryChunk('/2/more', router, dict(first='/b')),
            RouteHistoryChunk('/more', b, dict(second='/2')),
        ])
        self.assertEqual(child, app2)
        self.assertEqual(path, '/more')
        
        self.assertEqual(None, router.route('/a/extra'))
        try:
            router.route('/a/extra', strict=True)
            self.fail()
        except RoutingError as e:
            self.assertEqual(e.history, [
                RouteHistoryChunk('/a/extra', None, None),
                RouteHistoryChunk('/extra', router, dict(first='/a'))
            ])
            self.assertEqual(e.router, a)
            self.assertEqual(e.path, '/extra')
            
        app = webtest.TestApp(router)
        
        res = app.get('/a/1')
        self.assertEqual(res.body, 'one')
        res = app.get('/b/2')
        self.assertEqual(res.body, 'two')
        try:
            res = app.get('/b/4')
            self.fail()
        except HTTPNotFound as e:
            pass
        
        
        self.assertEquals('/a/1', router.url_for(**dict(first='a', second='1')))
        self.assertEquals('/b/2', router.url_for(**dict(first='b', second='2')))
        try:
            router.url_for(**dict(first='a'))
        except GenerationError as e:
            self.assertEquals(e.path, ['/a'])
            self.assertEquals(e.router, a)
            self.assertEquals(e.data, dict(first='a'))
        
        route, child, path = router.route('/a/1')
        
        self.assertEquals('/a/2', route.url_for(**dict(second='2')))
        self.assertEquals('/a/1', route.url_for(**dict(first='a')))
        self.assertEquals('/b/3', route.url_for(**dict(first='b', second='3')))
        try:
            x = route.url_for(**dict(first='b'))
            self.fail(x)
        except GenerationError as e:
            self.assertEquals(e.path, ['/b'])
            self.assertEquals(e.router, b)
            self.assertEquals(e.data, dict(first='b'))
            




if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
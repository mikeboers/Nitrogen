from nitrogen.core import App
from nitrogen import test
from nitrogen.request import Request, Response

class AppTests(test.TestCase):
    
    def test_simplest_app(self):
    
        app = App()
    
        @app.route(None)
        def do_render(request):
            return app.Response('hello')
    
        client = app.test_client()
        res = client.get('/')
    
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/html')
        self.assertEqual(res.data, 'hello')


    def test_args_dispatching(self):
    
        app = App()
    
        @app.route('/wsgi')
        def do_wsgi(environ, start):
            assert isinstance(environ, dict)
            start('200 OK', [])
            return ['wsgi']
        
        @app.route('/request')
        def do_request(request):
            assert isinstance(request, Request)
            return Response('request')
        
        @app.route('/none')
        def do_none():
            return 'none'
        
        client = app.test_client()
        self.assertEqual(client.get('/wsgi').data, 'wsgi')
        self.assertEqual(client.get('/request').data, 'request')
        self.assertEqual(client.get('/none').data, 'none')
        
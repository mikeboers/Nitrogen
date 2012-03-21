from nitrogen.core import App
from nitrogen import test

class TestCookies(test.TestCase):
    
    def test_simplest_cookie_app(self):
    
        app = App(test.app_config)
    
        @app.route('/set')
        def do_set(request):
            res = app.Response('cookies set')
            res.set_cookie('key', 'value')
            return res
    
        @app.route('/get')
        def do_get(request):
            return app.Response(request.cookies.get('key', 'no value'))
    
        client = app.test_client()
        
        res = client.get('/set')
        self.assertEqual(res.data, 'cookies set')
        
        res = client.get('/get')
        self.assertEqual(res.data, 'value')
    

from nitrogen.core import App


def test_simplest_app():
    
    app = App()
    
    @app.route(None)
    def do_render(request):
        return app.Response('hello')
    
    client = app.test_client()
    res = client.get('/')
    
    assert res.status_code == 200
    assert res.mimetype == 'text/html'
    assert res.data == 'hello'
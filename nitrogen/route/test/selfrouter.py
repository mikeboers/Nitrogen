
import webtest

from ..selfrouter import SelfRouter


def test_main():
    
    class TestRouter(SelfRouter):
        def do_index(self, environ, start):
            start('200 OK', [('Content-Type', 'text/plain')])
            yield 'index'
    
    router = TestRouter()
    
    # print router.route('')
    
    app = webtest.TestApp(router)
    res = app.get('/')
    # print repr(res.body)
    

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

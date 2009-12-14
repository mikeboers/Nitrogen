"""Reflection based WSGI router.

This class first pulls off an path segment that it will handle. Then, it
looks for an attribute on itself named "do_<segment>", and calls it.

If it can't find anything, it throws a NotFound error.

It is written so that you can nest reflectors.

"""

from webtest import TestApp as WebTester

from ..uri.path import Path
from . import tools

class SelfRouter(tools.Router):
    
    def __init__(self, route_key='self', default='action'):
        self.route_key=route_key
        self.default = default
    
    def route_step(self, path):
        path = Path(path)
        rawname = path[0] if path else self.default
        name = 'do_' + rawname
        if not hasattr(self, name):
            return
        return getattr(self, name), ''.join(path[1:]), {self.route_key: rawname}



def test_main():
    
    class TestRouter(SelfRouter):
        def do_index(self, environ, start):
            start('200 OK', [])
            yield 'index'
    
    router = TestRouter()
    
    print router.route('')
    
    app = WebTester(router)
    res = app.get('')
    print repr(res.body)
    

if __name__ == '__main__':
    from .. import test
    test.run()

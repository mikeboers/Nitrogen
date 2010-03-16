
import sys
from pprint import pprint

import webtest

from ..modulerouter import ModuleRouter
from .. import core
from ...http import status

class FakeModule(object):

    modules = []

    def __init__(self, name, output='', app=None):
        self.name = name
        self.output = output
        if app:
            self.app = app

        assert name not in sys.modules
        sys.modules[name] = self
        self.modules.append(self)
        
    @property
    def __name__(self):
        return self.name
        
    @property
    def __file__(self):
        return __file__

    @classmethod
    def cleanup(self):
        for mod in self.modules:
            del sys.modules[mod.name]
        del self.modules[:]

    def app(self, environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield self.output


def test_routing_path_setup():
    

    
    router = ModuleRouter()
    FakeModule('test_one', output='ONE')

    app = webtest.TestApp(router)

    res = app.get('/test_one/extra')
    assert res.body == 'ONE'
    
    core._assert_next_history_step(res,
            path='/extra',
            router=router
    )
    
    route = core.get_route(res.environ)
    pprint(route)
    print repr(route.url_for(controller='test_one'))
    

    try:
        app.get('/-does/not/exist')
        assert False
    except status.HttpNotFound:
        pass



if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
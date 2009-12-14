

import os
import re
import logging

from ..uri.path import Path
from ..http.status import HttpNotFound
from . import tools


log = logging.getLogger(__name__)


class Module(tools.Router):
    
    def __init__(self, router, module):
        self.router = router
        self.module = module
        self.app = None
        self.last_mtime = self.getmtime()
    
    def getmtime(self):
        return os.path.getmtime(self.module.__file__)
    
    def route_step(self, path):
        if self.router.reload:
            mtime = self.getmtime()
            if self.last_mtime != mtime:
                self.last_mtime = mtime
                self.app = None
                log.debug('reloading controller module %r' % self.module.__name__)
                reload(self.module)
        if self.app is None:
            self.app = getattr(self.module, self.router.app_key, None)
            if self.app is None:
                msg = 'could not find app %r on controller module %r' % (
                    self.app_key, self.module.__name__)
                log.debug(msg)
                return
        return self.app, path, {}
    
    def generate_step(self, data):
        return '', self.app


class ModuleRouter(tools.Router):
    
    def __init__(self, app_key='app', package='', default='index',
        reload=False, route_key='controller'):
        
        self.app_key = app_key
        self.package = package
        self.default = default
        self.reload = reload
        self.route_key = route_key
        
        self._modules = {}
    
    
    def route_step(self, path):
        
        path = Path(path)
        segment = path[0] if path else self.default
        segment = re.sub(r'[^a-zA-Z0-9_]+', '_', segment)
        name = '.'.join(filter(None, self.package.split('.') + [segment]))
        
        if name not in self._modules:
            try:
                raw_module = __import__(name, fromlist=['nonempty'])
            except ImportError as e:
                # This is my ugly attempt to only throw a 404 if this import
                # fails, and not some import that this impor triggers.
                if e.args[0] == 'No module named %s' % segment:
                    log.warning('could not import controller module %r: %r' % (name, e))
                    return
                else:
                    raise
            self._modules[name] = Module(router=self, module=raw_module)
        
        module = self._modules[name]
        
        if path:
            path.pop(0)
            path = str(path)
        else:
            path = ''
        
        return module, path, {self.route_key: segment}
    
    def generate_step(self, data):
        print 'ModuleRouter.generate_step', self, data
        if self.route_key not in data:
            return
        segment = data.get(self.route_key)
        x = self.route_step(segment)
        if not x:
            return
        return '/' + segment, x[0]



import sys
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

    app = TestApp(router)

    res = app.get('/test_one/extra')
    assert res.body == 'ONE'
    
    tools._assert_next_history_step(res,
            path='/extra',
            router=router
    )
    
    route = tools.get_route(res.environ)
    pprint(route)
    print repr(route.url_for(controller='test_one'))
    

    try:
        app.get('/-does/not/exist')
        assert False
    except HttpNotFound:
        pass



if __name__ == '__main__':
    from .. import test
    from webtest import TestApp
    from pprint import pprint
    test.run()

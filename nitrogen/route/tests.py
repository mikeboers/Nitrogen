
from pprint import pprint

from webtest import TestApp as WebTester

from . import *
from .tools import *
from .modulerouter import FakeModule
from ..http.status import HttpNotFound
from ..request import as_request
from .. import test


controller_router = ModuleRouter(package=__name__)
app = WebTester(controller_router)


rerouter = ReRouter()
FakeModule('%s.rerouter' % __name__, app=rerouter)


@rerouter.register('/get/{id:\d+}', action='get', _parsers=dict(id=int))
@as_request
def rerouter_get(req, res):
    res.start()
    yield 'rerouter: get %d' % req.route['id']

@rerouter.register('/list')
@as_request
def rerouter_list(req, res):
    res.start()
    yield 'rerouter: list'

@rerouter.register('/{action}')
@as_request
def rerouter_list(req, res):
    res.start()
    yield 'rerouter: %s' % action





def test_rerouter_get():
    
    res = app.get('/rerouter/get/12')
    assert res.body == 'rerouter: get 12'
    
    route = tools.get_route(res.environ)
    print route.url_for(id=24)



if __name__ == '__main__':
    test.run()

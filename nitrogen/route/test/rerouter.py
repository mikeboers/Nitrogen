  
from pprint import pprint

import webtest

from . import EchoApp, _assert_next_history_step
from ...http.status import HttpNotFound
from ...request import as_request
from ..core import *
from .. import core
from .modulerouter import FakeModule, ModuleRouter
from ..rerouter import *

    


rerouter = ReRouter()
app = webtest.TestApp(rerouter)

@rerouter.register('/get/{id:\d+}', action='get', _parsers=dict(id=int))
@as_request
def rerouter_get(req, res):
    res.start(as_text=True)
    yield 'get %d' % req.route['id']

@rerouter.register('/list')
@as_request
def rerouter_list(req, res):
    res.start(as_text=True)
    yield 'list'

@rerouter.register('/{action}')
@as_request
def rerouter_list(req, res):
    res.start(as_text=True)
    yield '%s' % req.route['action']

def test_rerouter_get():

    res = app.get('/get/12')
    assert res.body == 'get 12'
    
    res = app.get('/list')
    assert res.body == 'list'
    
    res = app.get('/something')
    assert res.body == 'something'

    route = core.get_route_history(res.environ)
    print route.url_for(id=24)







def test_routing_path_setup():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield core.get_route_data(environ)['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield '%02d' % core.get_route_data(environ)['num']

    @router.register(r'/{key:pre\}post}')
    def three(environ, start, *args, **kwargs):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield core.get_route_data(environ)['key']

    app = webtest.TestApp(router)

    res = app.get('/one/two')
    assert res.body == 'one'
    # pprint(core.get_history(res.environ))
    _assert_next_history_step(res,
            path='/two',
            router=router
    )

    res = app.get('/x-4/x-3/x-2/one')
    # print res.body
    assert res.body == '04'
    # pprint(core.get_history(res.environ))
    _assert_next_history_step(res,
        path='/x-3/x-2/one', router=router, _data={'num': 4})
    
    try:
        app.get('/-does/not/exist')
        assert False
    except HttpNotFound:
        pass

    try:
        app.get('/one_extra/does-not-exist')
        assert False
    except HttpNotFound:
        pass

    res = app.get('/pre}post')
    assert res.body == 'pre}post'


def test_route_building():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield core.get_route_history(environ)[-1]['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        kwargs = core.get_route_history(environ)[-1]
        start('200 OK', [('Content-Type', 'text-plain')])
        yield '%02d' % kwargs.data['num']

    @router.register('')
    def three(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'empty'

    app = webtest.TestApp(router)

    res = app.get('/x-1')
    route = core.get_route_history(res.environ)
    print repr(res.body)
    print repr(route.url_for(num=2))

    res = app.get('/x-1/one/blah')
    route = core.get_route_history(res.environ)
    pprint(route)
    print repr(res.body)
    print repr(route.url_for(word='two'))



if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

  
from pprint import pprint

import webtest

from . import EchoApp
from .. import *
from ...http.status import HttpNotFound
from ...request import as_request
from ..base import *
from .. import base
from .modulerouter import FakeModule

    
controller_router = ModuleRouter(package=__name__)
app = webtest.TestApp(controller_router)


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

    route = base.get_route(res.environ)
    print route.url_for(id=24)




def test_routing_path_setup():

    router = ReRouter()

    @router.register(r'/{word:one|two|three}')
    def one(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield base.get_route(environ)[-1]['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        chunk = base.get_route(environ)[-1]
        output = list(router(environ, start))
        yield '%02d\n' % chunk['num']
        for x in output:
            yield x

    @router.register(r'/{key:pre\}post}')
    def three(environ, start, *args, **kwargs):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield base.get_route(environ)[-1]['key']

    app = webtest.TestApp(router)

    res = app.get('/one/two')
    assert res.body == 'one'
    # pprint(base.get_history(res.environ))
    base._assert_next_history_step(res,
            path='/two',
            router=router
    )

    res = app.get('/x-4/x-3/x-2/one')
    # print res.body
    assert res.body == '04\n03\n02\none'
    # pprint(base.get_history(res.environ))
    base._assert_next_history_step(res,
        path='/x-3/x-2/one', router=router, _data={'num': 4})
    base._assert_next_history_step(res,
        path='/x-2/one', router=router, _data={'num': 3})
    base._assert_next_history_step(res,
        path='/one', router=router, _data={'num': 2})
    base._assert_next_history_step(res,
        path='', router=router, _data={'word': 'one'})

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
        yield base.get_route(environ)[-1]['word']

    @router.register(r'/x-{num:\d+}', _parsers=dict(num=int))
    def two(environ, start):
        kwargs = base.get_route(environ)[-1]
        start('200 OK', [('Content-Type', 'text-plain')])
        yield '%02d' % kwargs['num']

    @router.register('')
    def three(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield 'empty'

    app = webtest.TestApp(router)

    res = app.get('/x-1')
    route = base.get_route(res.environ)
    print repr(res.body)
    print repr(route.url_for(num=2))

    res = app.get('/x-1/one/blah')
    route = base.get_route(res.environ)
    pprint(route)
    print repr(res.body)
    print repr(route.url_for(word='two'))

if __name__ == '__main__':
    import logging
    import nose; nose.run(defaultTest=__name__)

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

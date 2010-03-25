from webtest import TestApp

from ..apache import *


def test_routing_path_setup():

    def app(environ, start):
        start('200 OK', [('Content-Type', 'text-plain')])
        yield environ.get('SCRIPT_NAME', '') + ':'
        yield environ.get('PATH_INFO', '')

    app = setup_apache_path_info(app)
    app = TestApp(app)

    res = app.get('/one/two')
    assert res.body == ':/one/two'

    res = app.get('//leading/and/trailing//')
    assert res.body == '://leading/and/trailing//'

    res = app.get('/one/two', extra_environ=dict(REQUEST_URI='/from/apache'))
    assert res.body == ':/from/apache'


if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

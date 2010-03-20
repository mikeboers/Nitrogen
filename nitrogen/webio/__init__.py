"""Web input parsing functions.

The functions and middleware in this module are designed to parse query string
(GET) and posted data/files. They do so in a lazy manner, only parsing the
input when they must. This gives a little bit of time to setup some
configuration on how the files are parsed.

By default, files are rejected; an exception is thrown when a file is posted.
If you want to accept files you must specify a make_file attribute on the
files object, which will be called with positional arguments `key` (the key it
will have in the files dict), `filename` (as reported by the browser), and
`length` (the content-length of the file as reported by the browser; may be
None). It is expected to return a file-like object.

There are two make_file functions provided: make_stringio and make_temp_file.

The file-like object returned from make_file is wrapped in a class which makes
sure that it only accepts as much data as we allow via the
`max_file_length` attribute. There is protection elsewhere to make sure that
the client reported length is smaller than the `max_file_length` but the client
need not provide it.

"""



import logging


log = logging.getLogger(__name__)


def request_params(app, parse_cookies=True, **kwargs):
    log.warning('request_params has been depreciated. use setup_cookies')
    if parse_cookies:
        from .cookies import setup_factory
        app = setup_factory(app, hmac_key=hmac_key)
    return app


def test_get():
    import webtest
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "START|"
        for k, v in environ.get('nitrogen.get').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = request_params(app)
    app = webtest.TestApp(app)
    
    res = app.get('/')
    assert res.body == 'START|END'
    
    res = app.get('/?key=value&key2=value2')
    assert res.body == 'START|key=value|key2=value2|END'

def test_post():
    import webtest
    def app(environ, start):
        start('200 OK', [('Content-Type', 'text/plain')])
        yield "START|"
        for k, v in environ.get('nitrogen.post').allitems():
            yield ('%s=%s|' % (k, v)).encode('utf8')
        yield "END"
    app = request_params(app)
    app = webtest.TestApp(app)
    
    res = app.post('/')
    assert res.body == 'START|END'
    
    res = app.post('/', 'key=value&same=first&same=second')
    assert res.body == 'START|key=value|same=first|same=second|END'
        

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
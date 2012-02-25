from . import *


cookies = [
    ('max_age', 'this has a max_age of 5 seconds after creation', dict(max_age=5)),
    ('unicode', u''.join(unichr(i) for i in range(512)), dict(max_age=60)),
    ('binary', ''.join(chr(i) for i in range(256)), dict(max_age=60)),
    ('is_httponly', 'this is http_only', dict(http_only=True, max_age=60)),
    ('is_secure', 'this one is secure', dict(secure=True, max_age=60)),
    ('no_path', 'this one has no path', dict(path=None, max_age=60)),
]

@route('/')
def do_cookies(request):
    def _do_cookies():
        yield "This is an example for testing cookies; refresh if you don't see anything.\n"
        yield "By playing with the escaping cookie I have determined that there\n"
        yield "is a maximum length to cookies, maybe around 2048 bytes.\n\n"
        
        yield "RAW COOKIES (with signatures visible):\n"
        for k, v in sorted(request.raw_cookies.items()):
            yield '\t%s: %r\n' % (k, v)
        yield "\n"
        
        yield "COOKIES (that pass verification):\n"
        for k, v in sorted(request.cookies.items()):
            yield '\t%s: %r\n' % (k, v)
        yield "\n"
        
        
        if request.cookies:
            good = True
            for name, value, _ in cookies:
                if name in request.cookies and request.cookies[name] != value:
                    yield 'MISMATCH on %r\n' % name
                    good = False
            if good:
                yield 'ALL COOKIES MATCH EXPECTED.'
        else:
            yield "NO COOKIES.\n"
    
    response = Response(''.join(_do_cookies()), mimetype='text/plain')
    
    for name, value, kwargs in cookies:
        response.set_cookie(name, value, **kwargs)
    
    if 'toggle' in request.cookies:
        response.delete_cookie('toggle')
    else:
        response.set_cookie('toggle', 'this cookie should not exist on the next request', max_age=60)
    
    response.set_cookie('counter', str(int(request.cookies.get('counter', 0)) + 1), max_age=60)
    
    return response


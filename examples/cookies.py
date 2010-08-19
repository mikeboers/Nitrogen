
from .app import app

from nitrogen.webio.cookies import parse_cookies

def cookie_app(environ, start):
    
    cookies = app.cookie_factory(environ.get('HTTP_COOKIE', ''))
    
    cookies['key'] = 'value'
    cookies.set('max_age', 'this has a max_age of 5 seconds after creation', max_age=5)
    cookies.set('escaped', ''.join(unichr(i) for i in range(512)), max_age=10)
    cookies.set('httponly', 'this is httponly', http_only=True)
    cookies.set('secure', 'this one is secure', secure=True)
    cookies.set('no_path', 'this one has no path', path=None)
    
    if 'toggle' in cookies:
        cookies['toggle'].expire()
    else:
        cookies['toggle'] = 1
    
    cookie_headers = cookies.build_headers()
    start('200 OK', [('Content-Type', 'text/plain')] + cookie_headers)
    
    
    yield "This is an example for testing cookies.\n"
    yield "The beast of the escaped cookie will expire in 10 seconds.\n"
    yield "\n"
    
    yield "By playing with the escaping cookie I have determined that there\n"
    yield "is a maximum length to cookies, maybe around 2048 bytes.\n\n"
    
    yield 'HTTP_COOKIE: %r\n' % environ.get('HTTP_COOKIE')
    yield "\n"
    
    yield "COOKIES:\n"
    for k, v in sorted(cookies.items()):
        yield '\t%s: %r\n' % (k, v.value)
    yield "\n"
    
    if 'escaped' in cookies:
        if cookies['escaped'].value == ''.join(unichr(i) for i in range(512)):
            yield "ESCAPED PROPERLY!\n\n"
        else:
            yield "ESCAPE FAILURE!\n\n"
    else:
        yield "Please refresh to see if the escaping runs properly...\n\n"

        
    yield "COOKIE HEADERS:\n"
    for k, v in cookie_headers:
        yield "\t%s: %s\n" % (k, v)
    yield "\n"
    
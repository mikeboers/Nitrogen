from . import *

@route('/')
def do_cookies(request):
    def _do_cookies():
        yield "This is an example for testing cookies.\n"
        yield "Refresh if you don't see anything.\n"
        # yield "The beast of the escaped cookie will expire in 10 seconds.\n"
        yield "\n"
    
        # yield "By playing with the escaping cookie I have determined that there\n"
        # yield "is a maximum length to cookies, maybe around 2048 bytes.\n\n"
        
        yield "RAW COOKIES:\n"
        for k, v in sorted(request.raw_cookies.items()):
            yield '\t%s: %r\n' % (k, v)
        yield "\n"
        
        yield "COOKIES (that pass verification):\n"
        for k, v in sorted(request.cookies.items()):
            yield '\t%s: %r\n' % (k, v)
        yield "\n"
        
        
        # if 'escaped' in request.cookies:
        #     if cookies['escaped'].value == ''.join(unichr(i) for i in range(512)):
        #         yield "ESCAPED PROPERLY!\n\n"
        #     else:
        #         yield "ESCAPE FAILURE!\n\n"
        # else:
        #     yield "Please refresh to see if the escaping runs properly...\n\n"
    
    response = Response(_do_cookies(), mimetype='text/plain')
    
    response.set_cookie('key', 'value')
    response.set_cookie('max_age', 'this has a max_age of 5 seconds after creation', max_age=5)
    # response.set_cookie('escaped', ''.join(unichr(i) for i in range(512)).encode('utf8'), max_age=10)
    response.set_cookie('is_httponly', 'this is httponly', httponly=True)
    response.set_cookie('is_secure', 'this one is secure', secure=True)
    response.set_cookie('no_path', 'this one has no path', path=None)
    
    if 'toggle' in request.cookies:
        response.delete_cookie('toggle')
    else:
        response.set_cookie('toggle', 'true')
    
    return response


import time

from . import *


@route('/')
def do_stream(request):
    def _do_stream():
        # Need a big block of text before it will start streaming the text to the user's window.
        yield '<!--'
        yield ' ' * 1024
        yield '-->\n'
        
        for i in range(10):
            yield '%d\n' % i
            time.sleep(0.1)
    
    return Response(_do_stream(), mimetype='text/html')

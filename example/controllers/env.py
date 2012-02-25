from . import *

@route('/')
def do_env(request):
    def _env():
        for x in sorted(request.environ.items()):
            yield '%s: %r\n' % x
    return Response(_env(), mimetype='text/plain')

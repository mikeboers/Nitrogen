from . import *

@route('/')
def do_session(request):
    count = request.session.get('counter', 0) + 1
    request.session['counter'] = count
    request.session.save()
    return Response('counter: %d' % count)

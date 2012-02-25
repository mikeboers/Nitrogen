from . import *

@route('/')
def do_index(request):
    return Response('Hello, world!')

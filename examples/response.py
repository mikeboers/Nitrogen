
from .app import *


def inner(request):
    yield 'Hello, world!\n'
    yield '\n'
    
@router.register('')
@router.register('/')
@Request.application
def cookie_app(request):
    res = Response(''.join(inner(request)))
    res.set_etag('hello')
    return res
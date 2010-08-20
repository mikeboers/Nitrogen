
from .app import *

from nitrogen.webio.cookies import parse_cookies

response_app = router = ReRouter()

@router.register('')
@router.register('/')
@as_request
def cookie_app(request, response):
    response.body = 'This is the body'
    return response('This is the second body')

from .app import *

from nitrogen.webio.cookies import parse_cookies

script_app = router = ReRouter()


    
@router.register('')
@router.register('/')
@Request.application
def do_jquery(request):
    return Response(render('/script/index.html'), as_html=True)

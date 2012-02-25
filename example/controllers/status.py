from . import *

from nitrogen import status


@route('/', code=418)
@route('/{code:\d+}', _parsers=dict(code=int))
def do_error(request):
    raise status.exceptions[request.route['code']]

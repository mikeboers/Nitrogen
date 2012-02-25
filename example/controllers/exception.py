from . import *


class TestError(ValueError):
    pass

@route('/', message='test exception')
@route('/{message:.+}')
def do_exception(request):
    raise TestError(request.route['message'])

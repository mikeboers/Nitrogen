from nitrogen import status
from . import *

@route('/show')
def do_show(request):
    def _show():
        msgs = request.app.get_flash_messages()
        yield '%d flash message(s)\n' % len(msgs)
        for cls, message in msgs:
            yield '%s: %r\n' % (cls, message)
    return Response(''.join(_show()), mimetype='text/plain')


@route('/', message='Default message.')
@route('/{message:.+}')
def do_flash(request):
    request.app.flash(request.route['message'])
    return status.SeeOther('/flash/show')



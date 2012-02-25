from . import *


@route('/')
def do_request(request):

    def _do_request():
        for key in dir(request):
            if key.startswith('_'):
                continue
            value = getattr(request, key)
            if hasattr(value, 'iteritems'):
                try:
                    items = list(value.iteritems())
                except TypeError:
                    yield '%s: %r\n' % (key, value)
                else:
                    yield '%s:\n' % key
                    for k, v in items:
                        yield '\t%s: %r\n' % (k, v)
            else:
                yield '%s: %r\n' % (key, value)

            yield '\n'
    
    return Response(_do_request(), mimetype='text/plain')


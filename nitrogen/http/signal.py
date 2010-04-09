
import sys

import paste.httpexceptions as base


# Pull in all the Paste exceptions.
self = sys.modules[__name__]
for name, obj in base.__dict__.iteritems():
    if name.startswith('HTTP') and issubclass(obj, base.HTTPException):
        setattr(self, name, obj)


        
def _force_iter_start_gen(first, iter):
    yield first
    for x in iter:
        yield x
        
def force_iter_start(iter):
    try:
        first = next(iter)
    except StopIteration:
        return []
    return _force_iter_start_gen(first, iter)


def default_signal_processor(environ, start, e):
    return e(environ, start)


def converter(primary_app, signal_processor=default_signal_processor):
    def converter_app(environ, start):
        try:
            return force_iter_start(app(environ, start))
        except HTTPException as e:
            return signal_processor(environ, start, e)
    return converter_app


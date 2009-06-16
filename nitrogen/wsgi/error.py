import sys
import traceback

def _reporter(environ, error=None, output=None):
    error = error if error else sys.exc_value
    yield 'UNCAUGHT %r\n\n' % error
    yield traceback.format_exc()
    yield '\n'
    yield 'Environment:\n'
    yield '\n'.join('  %s: %r' % x for x in sorted(environ.items()))
    if output:
        yield '\n\n'
        yield 'Recieved %d chunks (%d bytes).\n' % (len(output), sum(len(x) for x in output))
        yield '=' * 80 + '\n'
        for x in output:
            yield x
        if not x.endswith('\n'):
            yield '\n'
        yield '=' * 80

def format_error_report(environ, error=None, output=None):
    return ''.join(_reporter(environ, error, output))
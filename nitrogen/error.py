"""Module for dealing with WSGI errors."""

import sys
import traceback

def _reporter(environ, output=None):
    """Worker function for format_error_report.
    
    See format_error_report for details.
    """
    
    yield traceback.format_exc()
    yield '\n'
    yield 'Environment:\n'
    yield '\n'.join('  %s: %r' % x for x in sorted(environ.items()))
    if output is not None:
        output = list(output)
        yield '\n\n'
        yield 'Recieved %d chunks (%d bytes).' % (len(output), sum(len(x) for x in output))
        if output:
            yield '\n'
            yield '=' * 80 + '\n'
            for x in output:
                yield x
            if not x.endswith('\n'):
                yield '\n'
            yield '=' * 80

def format_error_report(environ, output=None):
    """Builds an error report with traceback, environment, and buffered
    output, if supplied.
    
    Params:
        environ -- The WSGI environ that the error occoured in.
        output -- The caught WSGI output (so far).
    """
    
    return ''.join(_reporter(environ, output))
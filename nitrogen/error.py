"""Module for dealing with WSGI errors."""

import sys
import traceback

from mako.exceptions import RichTraceback as MakoTraceback

def _reporter(environ, output=None):
    """Worker function for format_error_report.
    
    See format_error_report for details.
    """
    
    yield "Traceback (most recent call last):\n"
    for x in traceback.format_list(get_cleaned_traceback()):
        yield x
    type, value, tb = sys.exc_info()
    for x in traceback.format_exception_only(type, value):
        yield x
    
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
        yield '\n'

def format_error_report(environ, output=None):
    """Builds an error report with traceback, environment, and buffered
    output, if supplied.
    
    Params:
        environ -- The WSGI environ that the error occoured in.
        output -- The caught WSGI output (so far).
    """
    
    return ''.join(_reporter(environ, output))

def get_cleaned_traceback():
    """Gets a prepared traceback list.
    
    Processes it through the Mako RickTraceback to fix any mako stuff.
    """
    try:
        return list(MakoTraceback().traceback)
    except:
        type, value, traceback = sys.exc_info()
        return traceback.extrace_tb(traceback)
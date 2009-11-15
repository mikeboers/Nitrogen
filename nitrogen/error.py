"""Module for dealing with WSGI errors."""

# Setup path for local evaluation. Do not modify anything except for the name
# of the toplevel module to import at the very bottom.
if __name__ == '__main__':
    def __local_eval_setup(root, debug=False):
        global __package__
        import os, sys
        file = os.path.abspath(__file__)
        sys.path.insert(0, file[:file.find(root)].rstrip(os.path.sep))
        name = file[file.find(root):]
        name = '.'.join(name[:-3].split(os.path.sep)[:-1])
        __package__ = name
        if debug:
            print ('Setting up local environ:\n'
                   '\troot: %(root)r\n'
                   '\tname: %(name)r' % locals())
        __import__(name)
    __local_eval_setup('nitrogen', True)


import sys
import traceback
import logging

from mako.exceptions import RichTraceback as MakoTraceback


log = logging.getLogger(__name__)


DEFAULT_ERROR_HTTP_STATUS = '500 Internal Server Error'
DEFAULT_ERROR_HTTP_HEADERS = [('Content-Type','text/plain')]
DEFAULT_ERROR_BODY = """Uh oh... we dropped the ball on this one.

But don't worry! The site builders have been notified.

Please make your request again. If this error continues to occur please wait a
little while and try again.

Thank you for you patience as we resolve this matter.
"""

def build_error_report(environ, output=None):
    """Returns an iterator of consecutive parts of an error report with
    traceback, environment, and buffered output, if supplied.
    
    Must be called while handling an exception.
    
    Params:
        environ -- The WSGI environ that the error occoured in.
        output -- Any WSGI output captured.
    
    Example:
        >>> try:
        ...     raise ValueError('Testing')
        ... except:
        ...     print format_error_report({'HTTP_HOST': 'example.com'}, ['one', 'two'])
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "<doctest ....build_error_report[0]>", line 2, in <module>
            raise ValueError('Testing')
        ValueError: Testing
        Environment:
          HTTP_HOST: 'example.com'
        Sent 2 chunks (6 bytes):
        ==============================================================================
        onetwo
        ==============================================================================
        <BLANKLINE>
        
    """
    
    yield "Traceback (most recent call last):\n"
    for x in traceback.format_list(get_cleaned_traceback()):
        yield x
    type, value, tb = sys.exc_info()
    for x in traceback.format_exception_only(type, value):
        yield x
    
    # yield '\n'
    yield 'Environment:\n'
    yield '\n'.join('  %s: %r' % x for x in sorted(environ.items()))
    yield '\n'
    if output is not None:
        output = list(output)
        output_len = sum(len(x) for x in output)
        # yield '\n\n'
        yield 'Sent %d chunks (%d bytes)' % (len(output), sum(len(x) for x in output))
        if output_len:
            yield ':\n'
            yield '=' * 78 + '\n'
            for x in output:
                yield x
            if not x.endswith('\n'):
                yield '\n'
            yield '=' * 78
        else:
            yield '.'
        yield '\n'


def format_error_report(environ, output=None):
    """Returns a stringified error report as built by build_error_report."""
    return ''.join(build_error_report(environ, output))


def get_cleaned_traceback():
    """Returns a traceback cleaned of mako jibberish.
    
    Must be called from within an exception handler.
    
    """
    
    try:
        return list(MakoTraceback().traceback)
    except:
        type, value, traceback = sys.exc_info()
        return traceback.extract_tb(traceback)


def error_logger(app, level=logging.ERROR):
    """WSGI middleware which logs errors, environments, and caught output.

    Reraises the exception after logging it.

    """

    def inner(environ, start):
        output = []
        try:
            for x in app(environ, start):
                output.append(x)
                yield x
        except Exception as e:
            report = format_error_report(environ, output=output).strip()
            log.log(level, 'error_logger caught %r\n' % e + report)
            raise
    return inner


def error_notifier(app, render=None, traceback=False, template='_500.tpl'):
    """WSGI middleware to display a template to the client in case of error.

    If on a development server (server.is_dev is True), the template will also
    be passed the environment, the error, traceback, and caught output.    
    
    Note that this must buffer then entire response to work effectively.
    Note that this middleware does NOT rethrow the caught error.
    
    """
    
    class inner(object):
        
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.output = []
            self.status = None
            self.headers = None
        
        def app_start(self, status, headers):
            self.status = status
            self.headers = headers
        
        def __iter__(self):
            try:
                for x in app(self.environ, self.app_start):
                    self.output.append(x)
                self.start(self.status, self.headers or [])
                for x in self.output:
                    yield x
            except Exception as e:
                if render:
                    tb = get_cleaned_traceback()
                    try:
                        self.start('500 Internal Server Error', [('Content-Type',
                            'text/html; charset=UTF-8')])
                    except:
                        pass
                    yield render(template, **({
                        'environ': self.environ,
                        'error': e,
                        'traceback': tb,
                        'output': self.output
                        } if traceback else {})).encode('utf8')
                else:
                    report = format_error_report(self.environ)
                    try:
                        self.start('500 Internal Server Error', [('Content-Type',
                            'text/plain; charset=UTF-8')])
                    except:
                        pass
                    yield report
                    
    return inner

if __name__ == '__main__':
    from . import test
    test.run()
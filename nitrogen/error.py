"""Module for dealing with WSGI errors."""


from cgi import escape
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


def build_error_report(environ, output=None, html=False):
    """Returns an iterator of consecutive parts of an error report with
    traceback, environment, and buffered output, if supplied.
    
    Must be called while handling an exception.
    
    Params:
        environ -- The WSGI environ that the error occoured in.
        output -- Any WSGI output captured.
    
    Examples:
    
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
        Output 2 chunks (6 bytes):
        ==============================================================================
        onetwo
        ==============================================================================
        <BLANKLINE>
        
        
        >>> try:
        ...     raise ValueError('Testing')
        ... except:
        ...     print format_error_report(environ={'HTTP_HOST': 'example.com'}, output=['one', 'two'], html=True).replace('\\t', '    ')
        ... # doctest: +ELLIPSIS
        <h2>Traceback <em>(most recent call last)</em>:</h2>
        <ol>
            <li>
                File <strong>"&lt;doctest ....build_error_report[1]&gt;"</strong>, line <strong>2</strong>, in <strong>&lt;module&gt;</strong><br/>
                <code>raise ValueError('Testing')</code></li>
        </ol>
        <h3>ValueError: Testing</h3>
        <h2>Environment:</h2>
        <ul>
            <li><strong>HTTP_HOST</strong>: <code>'example.com'</code></li>
        </ul>
        <h2>Output <strong>2</strong> chunks (<strong>6</strong> bytes):</h2>
        <pre>onetwo</pre>
        
    """
        
    type, value, tb = sys.exc_info()
    
    if html:
        yield '<h2>Traceback <em>(most recent call last)</em>:</h2>\n'
        yield '<ol>\n'
        for filename, lineno, function, line in get_cleaned_traceback():
            yield '\t<li>\n'
            yield '\t\tFile <strong>"%s"</strong>, line <strong>%d</strong>, in <strong>%s</strong><br/>' % (escape(filename), lineno, escape(function))
            if line:
                yield '\n\t\t<code>%s</code>' % escape(line)
            yield '</li>\n'
        yield '</ol>\n'
        yield '<h3>'
        yield ''.join(traceback.format_exception_only(type, value)).strip()
        yield '</h3>\n'
        
    else:
        yield 'Traceback (most recent call last):\n'
        for x in traceback.format_list(get_cleaned_traceback()):
            yield x
        for x in traceback.format_exception_only(type, value):
            yield x
    
    if html:
        yield '<h2>Environment:</h2>\n'
        yield '<ul>\n'
        for k, v in sorted(environ.items()):
            yield '\t<li><strong>%s</strong>: <code>%s</code></li>\n' % (
                escape(str(k)), escape(repr(v)))
        yield '</ul>\n'
    
    else:
        yield 'Environment:\n'
        yield '\n'.join('  %s: %r' % x for x in sorted(environ.items()))
        yield '\n'
    
    if output is not None:
        output = list(output)
        output_len = sum(len(x) for x in output)
        
        if html:
            yield '<h2>Output <strong>%d</strong> chunk%s (<strong>%d</strong> bytes)%s</h2>\n' % (
                len(output), '' if len(output) == 1 else 's',
                output_len, ':' if output else ''
            )
            yield '<pre>'
            for x in output:
                yield x
            yield '</pre>'
        
        else:
            yield 'Output %d chunk%s (%d bytes)' % (len(output), '' if len(output) == 1 else 's', sum(len(x) for x in output))
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


def format_error_report(environ, output=None, html=False):
    """Returns a stringified error report as built by build_error_report."""
    return ''.join(build_error_report(environ=environ, output=output, html=html))


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

    def error_logger_app(environ, start):
        output = []
        try:
            for x in app(environ, start):
                output.append(x)
                yield x
        except Exception as e:
            report = format_error_report(environ, output=output).strip()
            log.log(level, 'error_logger caught %r\n' % e + report)
            raise
    return error_logger_app


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
        
        def error_notifier_start(self, status, headers, exc_info=None):
            self.status = status
            self.headers = headers
            if exc_info:
                logging.error(exc_info)
                
        def __iter__(self):
            try:
                for x in app(self.environ, self.error_notifier_start):
                    self.output.append(x)
                self.start(self.status, self.headers or [])
                for x in self.output:
                    yield x
            except Exception as e:
                
                text_report = format_error_report(self.environ, self.output)
                html_report = format_error_report(self.environ, self.output, html=True)
                
                try:
                    self.start('500 Internal Server Error', [('Content-Type',
                        'text/html; charset=UTF-8')])
                except:
                    pass
                
                if render:
                    try:
                        yield render(template, html_report=html_report if
                            traceback else None).encode('utf8')
                        if traceback:
                            yield '\n<!--\n\n'
                            yield text_report
                            yield '\n-->\n'
                        return
                    except Exception as e:
                        log.error('error while rendering error view', exc_info=sys.exc_info())
                        pass
                
                yield html_report
                yield '<!-- This is the same error report but in plaintext.\n\n'
                yield text_report
                yield '\n-->'
                    
    return inner

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
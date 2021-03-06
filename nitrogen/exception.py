"""Module for dealing with WSGI errors."""


from cgi import escape
import sys
import traceback
import logging
import os

try:
    from paste.httpexceptions import HTTPException as PasteException
except ImportError:
    class PasteException(object):
        pass

from werkzeug.datastructures import Headers
from mako.exceptions import RichTraceback as MakoTraceback, TopLevelLookupException as MakoLookupError

from . import status


log = logging.getLogger(__name__)


def safe_repr(x):
    try:
        return repr(x)
    except Exception as e:
        return "%s during repr: %s" % (e.__class__.__name__, e)


DEFAULT_ERROR_HTTP_STATUS = '500 Internal Server Error'
DEFAULT_ERROR_HTTP_HEADERS = [('Content-Type','text/plain')]
DEFAULT_ERROR_BODY = """Uh oh... we dropped the ball on this one.

But don't worry! The site builders have been notified.

Please make your request again. If this error continues to occur please wait a
little while and try again.

Thank you for you patience as we resolve this matter.
"""


def format_report_iter(environ, html=False):
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
        ...     print format_report({'HTTP_HOST': 'example.com'})
        ... # doctest: +ELLIPSIS
        Traceback (most recent call last):
          File "<doctest ....format_report_iter[0]>", line 2, in <module>
            raise ValueError('Testing')
        ValueError: Testing
        Environment:
          HTTP_HOST: 'example.com'
        <BLANKLINE>
        
        
        >>> try:
        ...     raise ValueError('Testing')
        ... except:
        ...     print format_report(environ={'HTTP_HOST': 'example.com'}, html=True).replace('\\t', '    ')
        ... # doctest: +ELLIPSIS
        <h2>Traceback <em>(most recent call last)</em>:</h2>
        <ol>
            <li>
                File <strong>"&lt;doctest ....format_report_iter[1]&gt;"</strong>, line <strong>2</strong>, in <strong>&lt;module&gt;</strong><br/>
                <code>raise ValueError('Testing')</code></li>
        </ol>
        <h3>ValueError: Testing</h3>
        <h2>Environment:</h2>
        <ul>
            <li><strong>HTTP_HOST</strong>: <code>'example.com'</code></li>
        </ul>
        <BLANKLINE>
        
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
                escape(str(k)), escape(safe_repr(v)))
        yield '</ul>\n'
    
    else:
        yield 'Environment:\n'
        for k, v in sorted(environ.items()):
            yield '  %s: %s\n' % (k, safe_repr(v))


def format_report(environ, html=False):
    """Returns a stringified error report as built by format_report_iter."""
    return ''.join(format_report_iter(environ, html))


def get_cleaned_traceback():
    """Returns a traceback cleaned of mako jibberish.
    
    Must be called from within an exception handler.
    
    """
    
    type, value, tb = sys.exc_info()
    try:
        raw = list(MakoTraceback().traceback)
    except:
        log.exception('Error while Mako was cleaning traceback')
        raw = traceback.extract_tb(tb)
    cleaned = []
    for filename, lineno, function, line in raw:
        cleaned.append((os.path.relpath(filename), lineno, function, line))
    return cleaned


def exception_logger(app, level=logging.ERROR, ignore=None):
    """WSGI middleware which logs errors, environments, and caught output.

    Reraises the exception after logging it. Ignored exceptions are still
    reraised.

    """
    
    ignore = ignore or ()
    def _exception_logger(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except ignore:
            raise
        except Exception as e:
            report = format_report(environ).strip()
            log.log(level, 'Unexpected %r\n' % e + report)
            raise
    
    return _exception_logger

error_logger = exception_logger
logger = exception_logger




def exception_handler(app, render=None, debug=False):
    def _exception_handler(environ, start):
        
        try:
            app_iter = iter(app(environ, start))
            try:
                yield next(app_iter)
            except StopIteration:
                pass
        except status.HTTPException as e:
            e.original = None
        except PasteException as original:
            e = status.exceptions.get(original.code) or status.InternalServerError
            e = e()
            e.original = original
        except Exception as original:
            e = status.InternalServerError()
            e.original = original
        else:
            for x in app_iter:
                yield x
            return
        
        if isinstance(e, status.HTTPRedirection):
            log.info('caught %d %s; redirects to %r' % (e.code, e.title, e.location))
            for x in e(environ, start):
                yield x
            return
        
        log.info('caught %d %s: %r' % (e.code, e.title, e.description))
        
        try:
            text_report = format_report(environ, False) if debug else None
            html_report = format_report(environ, True) if debug else None
        except:
            text_report = html_report = None
            log.exception('Exception while formating error report.')
        
        if render:
            output = None
            for template in ('/status/%d.html' % e.code, '/status/generic.html'):
                try:
                    output = render(template, exception=e,
                        environ=environ,
                        text_report=text_report,
                        html_report=html_report,
                    ).encode('utf8')
                except MakoLookupError:
                    continue
                except:
                    log.exception('Exception while building error page.')
                break
            if output:
                try:
                    start('%d %s' % (e.code, e.title), [('Content-Type', 'text/html; charset=utf-8')])
                except:
                    pass
                yield output
                return
            
        for x in e(environ, start):
            yield x
            
        # Need to break these out like this incase there was an issue while
        # building them.
        if html_report:    
            yield html_report
        if text_report:
            yield '<!-- This is the same error report but in plaintext.\n\n'
            yield text_report
            yield '\n-->'

    return _exception_handler

handler = exception_handler



class ExceptionAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(ExceptionAppMixin, self).__init__(*args, **kwargs)        
        self.register_middleware((self.FRAMEWORK_LAYER, 99), logger, None, dict(ignore=(status.HTTPException, )))
        self.register_middleware((self.FRAMEWORK_LAYER, 100), handler, None, dict(
            debug=self.config.debug,
            render=getattr(self, 'render', None),
        ))
        




if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)
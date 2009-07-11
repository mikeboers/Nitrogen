import logging
import traceback

from ..error import format_error_report
from ..view import render, TYPE_HEADER_HTML
from .. import config, server

def debugger(app):
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
                self.start(self.status, self.headers)
                for x in self.output:
                    yield x
            
            except Exception as e:
                report = format_error_report(self.environ, output=self.output)
                logging.error('nitrogen.wsgi.middlewear.debugger caught %r\n' % e + report)
                tb = traceback.format_exc()
                try:
                    self.start('500 Server Error', [
                        ('Content-Type', 'text/plain')
                    ])
                except:
                    pass
                yield report
    return inner


def server_error_catcher(app):
    """Catch all errors and display the _500.tpl template after logging.

    If on a development server, a stack trace and dump of the environment will
    be displayed along with an error message.

    Note that this must buffer then entire response to work effectively.
    """
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.output = []
            self.status = None
            self.headers = None
        def inner_start(self, status, headers):
            self.status = status
            self.headers = headers
        def __iter__(self):
            try:
                for x in app(self.environ, self.inner_start):
                    self.output.append(x)
                self.start(self.status, self.headers or [])
                for x in self.output:
                    yield x
            except Exception as e:
                logging.error('server_error_catcher caught %r\n' % (e, ) +
                    format_error_report(self.environ, output=self.output)
                )
                try:
                    self.start('500 Server Error', [TYPE_HEADER_HTML])
                except:
                    pass
                yield render('_500.tpl',
                    environ=self.environ if server.is_dev else None,
                    error=e if server.is_dev else None,
                    traceback=traceback.format_exc() if server.is_dev else None,
                    output=self.output if server.is_dev else None
                )
    return inner

def absolute_error_catcher(app):
    """Last resort error catcher.

    Does not display a nice looking message, but it is more robust in how it
    handles errors, so my hope is that this will catch errors within the
    higher level error catcher itself.

    This will attempt to send a critical log (which on production servers
    should result in an email being sent).

    Note that this must buffer the entire response.
    """
    def inner(environ, start):
        output = []
        try:
            for x in app(environ, start):
                output.append(x)
            for x in output:
                yield x
        except Exception as e:
            try:
                logging.critical('absolute_error_catcher caught %r\n' % e + format_error_report(environ, output=output))
            except:
                logging.critical(
                    'absolute_error_catcher caught an exception while logging an error report. WTF?!\n' +
                    traceback.format_exc()
                )
            try:
                start('500 Server Error', [])
            except:
                pass
            yield "\n"
            yield "A server error has occurred. The administrator has been notified.\n"
            yield "If this error continues to occur please wait a little while before trying again.\n"
            yield "\n"
            yield "Thank you for you understanding and support.\n"
            yield "\tThe Administrator."

    return inner
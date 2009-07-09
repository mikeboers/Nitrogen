import traceback
import logging
import zlib
import threading

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')

import nitrogen.cookie as cookie
from nitrogen.status import resolve_status
from nitrogen.error import format_error_report
import nitrogen.logs as logs

from nitrogen.route import NotFoundError

import nitrogen.view as view
from nitrogen.view import render, TYPE_HEADER_HTML

from nitrogen import config

from compressor import compressor
from input import input_parser

class log_extra_filler(object):
    def __init__(self, app):
        self.app = app
        self.thread_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        if not hasattr(logs.extra, 'thread_i'):
            self.lock.acquire()
            self.thread_count += 1
            logs.extra.thread_i = self.thread_count
            self.lock.release()
        logs.extra.ip = environ.get('REMOTE_ADDR')
        return self.app(environ, start)
                        
def utf8_encoder(app):
    """Encodes everything to a UTF-8 string.
    Forces test/* content types to have a UTF-8 charset.
    If there is not Content-Type, it adds a utf8 plain text one.
    """
    def inner(environ, start):
        def app_start(status, headers):
            has_type = False
            for i, h in enumerate(headers):
                if h[0] == 'Content-Type':
                    has_type = True
                    if h[1].startswith('text'):
                        if 'charset' not in h[1]:
                            headers[i] = (h[0], h[1] + ';charset=UTF-8')
                        elif 'UTF-8' not in h[1]:
                            raise ValueError('Content-Type header has non UTF-8 charset: %r.' % h[1])
            if not has_type:
                headers.append(('Content-Type', 'text/plain;charset=UTF-8'))
            start(status, headers)
        for x in app(environ, app_start):
            if not isinstance(x, unicode):
                x = unicode(x, 'utf8', 'replace')
            # TODO: Should this be ascii? Then all the unicode characters go as XML refs.
            yield x.encode('utf8', 'xmlcharrefreplace')
    return inner

def cookie_parser(app, hmac_key=None):
    class_ = cookie.make_signed_container(hmac_key) if hmac_key else cookie.Container
    def inner(environ, start):
        environ['nitrogen.cookies'] = class_(environ.get('HTTP_COOKIE', ''))
        return app(environ, start)    
    return inner

def cookie_builder(app, strict=True):
    class inner(object):
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.headers = None
    
        def inner_start(self, status, headers):
            cookies = self.environ.get('nitrogen.cookies')
            if cookies:
                self.headers = cookies.build_headers()
                headers.extend(self.headers)
            self.start(status, headers)
        
        def __iter__(self):    
            for x in app(self.environ, self.inner_start):
                yield x
            if not strict:
                return
            cookies = self.environ.get('nitrogen.cookies')
            if cookies is None:
                raise ValueError('Cookies have been removed from environ.')
            headers = cookies.build_headers()
            if self.headers is not None and self.headers != headers:
                raise ValueError('Cookies have been modified since WSGI start.', self.headers, headers)
    return inner

def full_parser(app, hmac_key=None, strict=True):
    return cookie_builder(
        input_parser(cookie_parser(app, hmac_key=hmac_key)),
        strict=strict
    )



def status_resolver(app):
    def inner(environ, start):
        def inner_start(status, headers):
            start(resolve_status(status), headers)
        return app(environ, inner_start)
    return inner

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



def straight_templater(app):
    """Look for a template at the path indicated by the request, and display
    it if found. Otherwise, play out the wrapped app like normal."""
    def inner(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except NotFoundError as e:
            uri = URI(environ.get('REQUEST_URI', ''))
            path = str(uri.path).lstrip('/') + '.tpl'
            if path.startswith('_'):
                raise
            fullpath = os.path.dirname(__file__) + '/app/view/' + path
            if not os.path.exists(fullpath):
                raise
            start('200 OK', [TYPE_HEADER_HTML])
            yield render(path)            
    return inner

def not_found_catcher(app):
    """Displays the _404.tpl template along with a "404 Not Found" status if a
    NotFoundError is thrown within the app that it wraps. This error is
    normally thrown by routers.
    """
    def inner(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except NotFoundError as e:
            logging.warning(repr(e))
            start('404 Not Found', [TYPE_HEADER_HTML])
            yield render('_404.tpl')
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
                self.start(self.status, self.headers)
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
                    environ=self.environ if config.is_dev else None,
                    error=e if config.is_dev else None,
                    traceback=traceback.format_exc() if config.is_dev else None,
                    output=self.output if config.is_dev else None
                )
    return inner

def environ_config(app):
    """Adds a number of app-specific items to the environ dict."""
    def inner(environ, start):
        environ['app.config'] = config
        environ['app.server'] = config.server
        return app(environ, start)
    return inner

def template_context_setup(app):
    """Adds a number of items from the environ to the template envionment.

    Adds:
        - environ
        - config
        - server
        - admin (None, or an instance of the User model)
    """
    def inner(environ, start):
        view.defaults.update(dict(
            environ=environ,
            config=config,
            server=config.server,
            user=environ.get('app.user')
        ))
        return app(environ, start)
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

if __name__ == '__main__':
    from nitrogen.test import run
    run()

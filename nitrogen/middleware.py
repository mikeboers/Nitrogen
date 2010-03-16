
import logging
import hashlib

from .request import as_request, Request, Response
from .headers import Headers
from .compressor import compressor
from .encoding import utf8_encoder
from .http.status import status_resolver, HttpNotFound
from .error import error_logger, error_notifier
from .webio import cookie_parser, cookie_builder, request_params, get_parser, post_parser
from .view import TYPE_HEADER_HTML
from .session import session_wrapper

log = logging.getLogger(__name__)


def etagger(app):
    def etagger_app(environ, start):
        
        state = dict(
            status=None,
            headers=None
        )
        def inner_start(status, headers, exc_info=None):
            state.update(dict(
                status=status,
                headers=headers
            ))
        
        output = ''.join(app(environ, inner_start))
        if isinstance(output, unicode):
            output = output.encode('utf8')
        
        # If the status is anything but a 200 OK then don't touch it.
        code = int(str(state['status']).split()[0])
        if code != 200:
            start(state['status'], state['headers'])
            yield output
            return
        
        etag = 'md5=' + hashlib.md5(output).hexdigest()
        
        req = Request(environ=environ)
        res = Response(start=start, headers=state['headers'])
        
        if res.etag is None:
            res.etag = etag
            if req.etag == etag:
                res.start('304 Not Modified')
                return
        
        res.start(state['status'])
        yield output
    
    return etagger_app
        
def output_buffer(app):
    """WSGI middleware which buffers all output before sending it on.
    
    The entire sub-app is completely exhausted before anything is returned
    from this. This allows you to call for WSGI start after you output, and
    multiple times (only the args from the last call are sent on).
    
    This behaviour is exhibited by quite a few other WSGI middlewares.
    
    """
    
    class output_buffer_app(object):
        
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.start_args = None
            self.start_kwargs = None
            
        def inner_start(self, *args, **kwargs):
            self.start_args = args
            self.start_kwargs = kwargs
            
        def __iter__(self, ):
            output = ''.join(app(self.environ, self.inner_start))
            self.start(*self.start_args, **self.start_kwargs)
            yield output
    
    return output_buffer_app

def not_found_catcher(app, render):
    """Displays the _404.tpl template along with a "404 Not Found" status if a
    HttpNotFound is thrown within the app that it wraps. This error is
    normally thrown by routers.
    """
    def not_found_catcher_app(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except HttpNotFound as e:
            log.info('caught HttpNotFound', exc_info=e)
            start('404 Not Found', [TYPE_HEADER_HTML])
            yield render('_404.tpl')
    return not_found_catcher_app        

if __name__ == '__main__':
    import nose; nose.run(defaultTest=__name__)

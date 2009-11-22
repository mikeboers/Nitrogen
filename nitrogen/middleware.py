

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
    def inner(environ, start):
        
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
        etag = 'auto-md5:' + hashlib.md5(output).hexdigest()
        
        log.debug(state['headers'])
        req = Request(environ=environ)
        res = Response(start=start, headers=state['headers'])
        
        res.etag = res.etag or etag
        
        if req.etag == etag:
            res.start('not modified')
            return
        
        res.start(state['status'])
        yield output
    
    return inner
        
def output_buffer(app):
    """WSGI middleware which buffers all output before sending it on.
    
    The entire sub-app is completely exhausted before anything is returned
    from this. This allows you to call for WSGI start after you output, and
    multiple times (only the args from the last call are sent on).
    
    This behaviour is exhibited by quite a few other WSGI middlewares.
    
    """
    
    class inner(object):
        
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.start_args = None
            self.start_kwargs = None
            
        def app_start(self, *args, **kwargs):
            self.start_args = args
            self.start_kwargs = kwargs
            
        def __iter__(self, ):
            output = ''.join(app(self.environ, self.app_start))
            self.start(*self.start_args, **self.start_kwargs)
            yield output
    
    return inner

def not_found_catcher(app, render):
    """Displays the _404.tpl template along with a "404 Not Found" status if a
    HttpNotFound is thrown within the app that it wraps. This error is
    normally thrown by routers.
    """
    def inner(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except HttpNotFound as e:
            log.info('caught HttpNotFound', exc_info=e)
            start('404 Not Found', [TYPE_HEADER_HTML])
            yield render('_404.tpl')
    return inner        

if __name__ == '__main__':
    from . import test
    test.run()

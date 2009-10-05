

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import logging

from .route import NotFoundError

from .views import render, TYPE_HEADER_HTML

from .compressor import compressor
from .encoding import utf8_encoder
from .status import status_resolver
from .error import error_logger, error_notifier
from .webio import cookie_parser, cookie_builder, request_params, get_parser, post_parser

def output_buffer(app):
    """WSGI middlewear which buffers all output before sending it on.
    
    The entire sub-app is completely exhausted before anything is returned
    from this. This allows you to call for WSGI start after you output, and
    multiple times (only the args from the last call are sent on).
    
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
            logging.getLogger(__name__).warning(repr(e))
            start('404 Not Found', [TYPE_HEADER_HTML])
            yield render('_404.tpl')
    return inner        

if __name__ == '__main__':
    from nitrogen.test import run
    run()

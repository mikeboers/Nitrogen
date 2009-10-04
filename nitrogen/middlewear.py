

# Setup path for local evaluation.
# When copying to another file, just change the __package__ to be accurate.
if __name__ == '__main__':
    import sys
    __package__ = 'nitrogen'
    sys.path.insert(0, __file__[:__file__.rfind('/' + __package__.split('.')[0])])
    __import__(__package__)

import traceback
import logging
import zlib
import threading

from .status import resolve_status
from .route import NotFoundError

from .views import render, TYPE_HEADER_HTML

from . import config, server

from .compressor import compressor
from .encoding import utf8_encoder
from .status import status_resolver
from .error import error_logger, error_notifier
from .webio import cookie_request_wrapper, cookie_response_wrapper, request_param_wrapper, full_parser

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

if __name__ == '__main__':
    from nitrogen.test import run
    run()

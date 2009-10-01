import traceback
import logging
import zlib
import threading

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')
    import nitrogen.middlewear as junk
    __package__ = 'nitrogen.middlewear'


from ..status import resolve_status
from ..route import NotFoundError

from .. import views
from ..views import render, TYPE_HEADER_HTML
from ..uri import URI

from .. import config, server

# Old middlewear that needs moving out of this package.
from .input import cookie_request_wrapper, cookie_response_wrapper, request_param_wrapper, full_parser
from .error import debugger, server_error_catcher, absolute_error_catcher

# Newly placed middlewear.
from ..compressor import compressor
from ..encoding import utf8_encoder
from ..status import status_resolver


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

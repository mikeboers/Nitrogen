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
from .input import cookie_parser, cookie_builder, input_parser, full_parser
from .unicode import utf8_encoder
from .error import debugger, server_error_catcher, absolute_error_catcher
from .view import straight_templater

# Newly placed middlewear.
from ..compressor import compressor

def wsgi_style(app):
    def inner(*args):
        if len(args) == 1:
            req = args[0]
            return app(req.environ, req.start)
        return app(*args)
    return inner

def status_resolver(app):
    def inner(environ, start):
        def inner_start(status, headers):
            start(resolve_status(status), headers)
        return app(environ, inner_start)
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

if __name__ == '__main__':
    from nitrogen.test import run
    run()

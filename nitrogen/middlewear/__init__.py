import traceback
import logging
import zlib
import threading

if __name__ == '__main__':
    import sys
    sys.path.insert(0, '../..')


from nitrogen.status import resolve_status

from nitrogen.route import NotFoundError

import nitrogen.view as view
from nitrogen.view import render, TYPE_HEADER_HTML

from compressor import compressor
from input import cookie_parser, cookie_builder, input_parser, full_parser
from logs import log_extra_filler
from unicode import utf8_encoder
from error import debugger, server_error_catcher, absolute_error_catcher
from view import template_context_setup, straight_templater

                        





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

def environ_config(app):
    """Adds a number of app-specific items to the environ dict."""
    def inner(environ, start):
        environ['nitrogen.config'] = nitrogen.config
        environ['nitrogen.server'] = nitrogen.server
        # environ['nitrogen.local']  = nitrogen.local
        return app(environ, start)
    return inner





if __name__ == '__main__':
    from nitrogen.test import run
    run()

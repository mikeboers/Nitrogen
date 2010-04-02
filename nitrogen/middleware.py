
import logging

from .http.status import HttpNotFound
from .view import TYPE_HEADER_HTML

log = logging.getLogger(__name__)



        


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

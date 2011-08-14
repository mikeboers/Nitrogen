
from urllib import urlencode
from urlparse import parse_qsl as urldecode 
import logging
import os

from .request import Request, Response
from . import status


PIXEL = '47494638396101000100800000000000ffffff2c00000000010001000002014c003b'.decode('hex')
PIXEL_MIMETYPE = 'image/gif'


class TrackerAppMixin(object):
    
    def __init__(self, *args, **kwargs):
        super(TrackerAppMixin, self).__init__(*args, **kwargs)
        
        self.tracker_log = logging.getLogger(self.config.tracker_log_name)

        if self.config.cookie_tracker_on:
            self.register_middleware((self.FRAMEWORK_LAYER, 10000), self.cookie_tracker_middleware)
        
        self.router.register(self.config.pixel_tracker_route, self.handle_tracking_pixel)
        self.view_globals['pixel_tracker_html'] = '<img id="tpixel" src="%s" />' % self.config.pixel_tracker_route
        
    
    def setup_config(self):
        super(TrackerAppMixin, self).setup_config()
        self.config.setdefaults(
            cookie_tracker_on=True,
            cookie_tracker_name='tracker',
            pixel_tracker_route='/tpixel.gif',
            tracker_log_name='http.tracker',
        )
    
    def cookie_tracker_middleware(self, app):
        def _app(environ, start):
            def _start(status, headers, *args):
                request = self.Request(environ)
                token = request.cookies.get(self.config.cookie_tracker_name)
                if not token:
                    token = os.urandom(16).encode('hex')
                    self.tracker_log.info('new token %s -> %s' % (token, request.user_agent))
                    response = self.Response()
                    response.cookies.set(self.config.cookie_tracker_name, token, path='/')
                    headers.extend(response.cookies.build_headers())
                self.set_access_log_meta(token=token)
                return start(status, headers, *args)
            return app(environ, _start)
        return _app
    
    @Request.application
    def handle_tracking_pixel(self, request):
        
        if request.if_none_match:
            
            token = list(request.if_none_match)[0]
            self.tracker_log.info('old etag %s' % token)
            return status.NotModified()
        
        token = os.urandom(16).encode('hex')
        self.tracker_log.info('new etag %s -> %s' % (token, request.user_agent))
            
        response = Response(PIXEL, mimetype=PIXEL_MIMETYPE)
        response.set_etag(token)
        response.private = True
        
        return response
    
    
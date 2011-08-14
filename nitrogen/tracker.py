
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
        self.router.register(self.config.tracker_route, self.handle_tracking_pixel)
        self.tracker_log = logging.getLogger(self.config.tracker_log_name)
        self.view_globals['tracker_html'] = '<img id="tpixel" src="%s" />' % self.config.tracker_route
    
    def setup_config(self):
        super(TrackerAppMixin, self).setup_config()
        self.config.setdefaults(
            tracker_log_name='http.tracker',
            tracker_route='/tpixel.gif',
        )
    
    @Request.application
    def handle_tracking_pixel_with_meta(self, request):
        
        if request.if_none_match:
            
            token = list(request.if_none_match)[0]
            
            if '?' in token:
                id, raw_query = token.split('?')
            else:
                id = token
                raw_query = ''
            query = dict(urldecode(raw_query))
            query['n'] = int(query.get('n', 0)) + 1
            
            new_token = id + '?' + urlencode(query)
            
            self.tracker_log.info('old token %s' % new_token)
            
            response = Response()
            response.status_code = status.NotModified.code
            response.set_etag(new_token)
            response.private = True
            return response
        
        token = '%s?n=1' % os.urandom(16).encode('hex')
        self.tracker_log.info('new token %s -> %s' % (token, request.user_agent))
            
        response = Response(PIXEL, mimetype=PIXEL_MIMETYPE)
        response.set_etag(token)
        response.private = True
        
        return response
    
    
    @Request.application
    def handle_tracking_pixel(self, request):
        
        if request.if_none_match:
            
            token = list(request.if_none_match)[0]
            self.tracker_log.info('old token %s' % token)
            return status.NotModified()
        
        token = os.urandom(16).encode('hex')
        self.tracker_log.info('new token %s -> %s' % (token, request.user_agent))
            
        response = Response(PIXEL, mimetype=PIXEL_MIMETYPE)
        response.set_etag(token)
        response.private = True
        
        return response
    
    
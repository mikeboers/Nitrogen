
from pprint import pprint
import logging

from ..uri.query import Query
from .maprouter import MapRouter
from .base import Router


log = logging.getLogger(__name__)


class Signer(Router):
    
    def __init__(self, app, key=(__file__ + __name__)):
        self.app = app
        self.key = key
    
    def route_step(self, path):
        try:
            path, rawquery = path.rsplit('/', 1)
            query = Query(rawquery)
            query['path'] = path
            if query.verify(key=self.key):
                return self.app, path, {}
            else:
                log.warning('path %r did not match signature %r' % (path, rawquery))
        except:
            log.exception('error while verifying path signature')
    
    def generate_step(self, data):
        return '', self.app
    
    def modify_path(self, path):
        print 'Signer.modify_path', path
        query = Query()
        query['path'] = path
        query.sign(key=self.key, add_time=False, nonce_bits=64)
        del query['path']
        return path + '/' + str(query)


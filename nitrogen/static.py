
import os
import logging

import webstar.core as core

from .request import Request, Response


log = logging.getLogger(__name__)

        
class StaticRouter(core.RouterInterface):
    
    use_x_sendfile = 'USE_X_SENDFILE' in os.environ
    
    def __init__(self, path, data_key='filename', use_x_sendfile=None,
        cache_max_age=3600
    ):
        self.path = map(os.path.abspath, path)
        self.data_key = data_key
        if use_x_sendfile is not None:
            self.use_x_sendfile = use_x_sendfile
        self.cache_max_age = cache_max_age
        super(StaticRouter, self).__init__()

    def get_mtime(self, path):
        path = path.lstrip('/')
        for base in self.path:
            fullpath = os.path.join(base, path)
            if os.path.exists(fullpath) and os.path.isfile(fullpath):
                return os.path.getmtime(fullpath)
        return None
    
    def route_step(self, path):
        path = path[1:]
        if not path:
            return
        for base in self.path:
            fullpath = os.path.join(base, path)
            if os.path.exists(fullpath) and os.path.isfile(fullpath):
                yield core.RouteStep(
                    head=_StaticApp(fullpath, self),
                    router=self,
                    consumed=path,
                    unrouted='',
                    data={self.data_key: path},
                )
    
    def generate_step(self, data):
        path = data.get(self.data_key)
        if path is not None:
            yield core.GenerateStep(segment=path, head=None)


class _StaticApp(object):

    def __init__(self, path, router):
        self.path = path
        self.router = router

    @Request.application
    def __call__(self, request):
        
        return Response().send_file(self.path,
            use_x_sendfile=self.router.use_x_sendfile,
            cache_max_age=self.router.cache_max_age,
        ).make_conditional(request)


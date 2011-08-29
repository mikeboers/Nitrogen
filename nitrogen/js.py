import os
import hashlib

from jsmin import jsmin

from . import status


class JavaScriptAppMixin(object):
    
    def setup_config(self):
        super(JavaScriptAppMixin, self).setup_config()
        self.config.setdefaults(
            jsmin_prefixes=['js', 'script'],
            jsmin_path=[],
            jsmin_route='/jsmin',
            jsmin_cache=self.config.cache_dir + '/jsmin',
        )
    
    def __init__(self, *args, **kwargs):
        super(JavaScriptAppMixin, self).__init__(*args, **kwargs)
        
        if not os.path.exists(self.config.jsmin_cache):
            os.makedirs(self.config.jsmin_cache)
        
        for prefix in self.config.jsmin_prefixes:
            for dir in self.config.static_path:
                path = os.path.join(dir, prefix)
                if os.path.exists(path):
                    self.config.jsmin_path.append(path)
        
        print self.config.jsmin_path
        
        self.router.register(self.config.jsmin_route, self.Request.application(self.do_jsmin))
    
    def find_js(self, local):
        for dir in self.config.jsmin_path:
            path = os.path.join(dir, local.strip('/'))
            print path
            if os.path.exists(path):
                return path
    
    def do_jsmin(self, request):
        
        path = self.find_js(request.path_info)
        if not path:
            return status.NotFound()
        
        cache_path = os.path.join(self.config.jsmin_cache, hashlib.md5(path).hexdigest() + '/js')
        return self.Response(path + ' ' + cache_path)



from webstar import Router

class ModuleRouter(Router):
    
    def __init__(self, app_key='__app__', package='', default='index',
        reload=False, route_key=None, data_key='controller'):
        
        data_key = route_key or data_key
        super(ModuleRouter, self).__init__()
        self.register_package('', package,
            data_key=data_key,
        )
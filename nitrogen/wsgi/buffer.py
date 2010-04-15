
def output_buffer(app):
    """WSGI middleware which buffers all output before sending it on.
    
    The entire sub-app is completely exhausted before anything is returned
    from this. This allows you to call for WSGI start after you output, and
    multiple times (only the args from the last call are sent on).
    
    This behaviour is exhibited by quite a few other WSGI middlewares.
    
    """
    
    class output_buffer_app(object):
        
        def __init__(self, environ, start):
            self.environ = environ
            self.start = start
            self.start_args = None
            
        def inner_start(self, *args):
            self.start_args = args
            
        def __iter__(self, ):
            output = ''.join(app(self.environ, self.inner_start))
            self.start(*self.start_args)
            yield output
    
    return output_buffer_app
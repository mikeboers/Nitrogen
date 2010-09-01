
from ..uri import URI

def setup_apache_path_info(app):
    """Clears out the SCRIPT_NAME, and sets PATH_INFO to the value in REQUEST_URI.
    
    This is effective if you are redirecting all requests that do not refer to
    existing files into a Python process, and want the URLs to be relative to
    the server root.
    
    """
    def setup_apache_path_info_app(environ, start):
        if 'REQUEST_URI' in environ:
            path = str(URI(environ['REQUEST_URI']).path)
        else:
            path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        environ['PATH_INFO'] = path
        environ['SCRIPT_NAME'] = ''
        return app(environ, start)
    return setup_apache_path_info_app

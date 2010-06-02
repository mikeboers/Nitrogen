
from ..uri import URI

def setup_apache_path_info(app):
    def setup_apache_path_info_app(environ, start):
        if 'REQUEST_URI' in environ:
            path = str(URI(environ['REQUEST_URI']).path)
        else:
            path = environ.get('SCRIPT_NAME', '') + environ.get('PATH_INFO', '')
        environ['PATH_INFO'] = path
        environ['SCRIPT_NAME'] = ''
        return app(environ, start)
    return setup_apache_path_info_app

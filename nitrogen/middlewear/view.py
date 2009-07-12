
from .. import views
from ..views import render, TYPE_HEADER_HTML
from .. import config

def straight_templater(app):
    """Look for a template at the path indicated by the request, and display
    it if found. Otherwise, play out the wrapped app like normal."""
    def inner(environ, start):
        try:
            for x in app(environ, start):
                yield x
        except NotFoundError as e:
            uri = URI(environ.get('REQUEST_URI', ''))
            path = str(uri.path).lstrip('/') + '.tpl'
            if path.startswith('_'):
                raise
            fullpath = os.path.dirname(__file__) + '/app/view/' + path
            if not os.path.exists(fullpath):
                raise
            start('200 OK', [TYPE_HEADER_HTML])
            yield render(path)            
    return inner
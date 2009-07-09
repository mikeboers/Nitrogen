
from .. import view
from ..view import render, TYPE_HEADER_HTML
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

def template_context_setup(app):
    """Adds a number of items from the environ to the template envionment.

    Adds:
        - environ
        - config
        - server
        - admin (None, or an instance of the User model)
    """
    def inner(environ, start):
        view.defaults.update(dict(
            environ=environ,
            config=config,
            server=config.server,
            user=environ.get('app.user')
        ))
        return app(environ, start)
    return inner
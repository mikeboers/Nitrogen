"""
Module for the most basic startup of nitrogen apps.

These should be the very first middlewear added. They will be added
automatically by the runners.

"""


from .. import local

def setup_local(app):
    def inner(environ, start):
        local.environ = environ
        local.start = start
        return app(environ, start)
    return inner
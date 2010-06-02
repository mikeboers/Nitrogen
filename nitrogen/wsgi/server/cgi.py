
from wsgiref.handlers import CGIHandler as _CGIServer
from ... import error

class CGIServer(_CGIServer):

    error_status = error.DEFAULT_ERROR_HTTP_STATUS
    error_headers = error.DEFAULT_ERROR_HTTP_HEADERS
    error_body = error.DEFAULT_ERROR_BODY

    def __init__(self, app):
        _CGIServer.__init__(self)
        self.app = app

    def run(self):
        _CGIServer.run(self, self.app)
import logging


log = logging.getLogger(__name__)


def buffer_output(app):
    def _buffer_output(*args):
        log.warning('buffer_output has been deprecated. Output was not buffered.')
        return app(*args)
    return _buffer_output

output_buffer = buffer_output
"""Logging module.

There are functions in here to setup the main methods of logging. The example
webapp runs them during it's setup procedure.

There is a log_extra_filler in middleware to fill in the IP and thread_i onto
the "extra" object so they will be in the logs.

"""

import os
import sys
import logging
import logging.handlers
import threading
import multiprocessing
import time


from . import app


base_format = "%(asctime)s %(levelname)-8s pid:%(process)d req:%(request_index)d ip:%(remote_addr)s %(name)s - %(message)s"


class ThreadLocalFormatter(logging.Formatter):
    
    @staticmethod
    def _build_local():
        return threading.local().__dict__
    
    @staticmethod
    def _build_lock():
        return threading.Lock()
    
    def __init__(self, *args, **kwargs):
        logging.Formatter.__init__(self, *args, **kwargs)
        
        self.local_extra = self._build_local()
        self.request_count = 0
        self.request_count_lock = self._build_lock()
        
    def format(self, record):
        data = {
            'remote_addr': None,
            'request_index': 0,
            'process': 0,
            'asctime': '<DATETIME>',
            'levelname': '<LEVELNAME>',
            'message': '<MESSAGE>'
        }
        data.update(self.local_extra)
        data.update(record.__dict__)
        
        if '%(asctime)' in base_format:
            data['asctime'] = self.formatTime(record)
        try:
            data['message'] = record.msg % record.args
        except:
            data['message'] = record.msg
        
        message = base_format % data
        
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if message[-1] != "\n":
                message += "\n"
            message += record.exc_text
        
        return message
    
    def init_request(self, environ):    
        with self.request_count_lock:
            self.request_count += 1
            self.local_extra['request_index'] = self.request_count
            self.local_extra['remote_addr'] = environ.get('REMOTE_ADDR')
        
    def wsgi_setup(self, app):
        def ThreadLocalFormatter_wsgi_setup_app(environ, start):
            self.init_request(environ)
            return app(environ, start)
        return ThreadLocalFormatter_wsgi_setup_app
    
    # For reverse compatibility.
    setup_wsgi = wsgi_setup

class ProcLocalFormatter(ThreadLocalFormatter):
    
    @staticmethod
    def _build_local():
        return dict()
    
    @staticmethod
    def _build_lock():
        return multiprocessing.Lock()


class FileHandler(logging.Handler):
    """File log handler which writes out to a path after running it
    through time.strftime.
    
    Tests to see if this path changes for every log
    so that records will always end up in the right file.
    """
    def __init__(self, path_format):
        logging.Handler.__init__(self)
        self.path_format = path_format
        self.fh = None
        self.last_path = None
    
    def emit(self, record):
        path = time.strftime(self.path_format, time.localtime(record.created))
        if path != self.last_path:
            if self.fh:
                self.fh.close()
            if not os.path.exists(path):
                open(path, 'wb').close()    
                os.chmod(path, 0777)
            self.fh = open(path, 'ab')
        self.last_path = path
        
        self.fh.write(self.format(record))
        self.fh.write('\n')
        self.fh.flush()


class LoggingAppMixin(app.Core):
    
    base_config = {
        'log_levels': {
            '': logging.DEBUG,
            'nitrogen.webio': logging.INFO,
            'nitrogen.route': logging.WARNING,
        },
        'log_handlers': [logging.StreamHandler(sys.stderr)],
    }
    
    def __init__(self, *args, **kwargs):
        super(LoggingAppMixin, self).__init__(*args, **kwargs)
        self._setup_handlers = []
        if not self.config.log_formatter:
            self.config['log_formatter'] = ThreadLocalFormatter()
        self.setup_logging()
    
    def setup_logging(self):
        self.log_formatter = self.config.log_formatter
        for name, level in self.config['log_levels'].items():
            logging.getLogger(name).setLevel(level)
        handlers = self.config['log_handlers'][:]
        root = logging.getLogger()
        for handler in self._setup_handlers:
            root.removeHandler(handler)
        self._setup_handlers = handlers
        for handler in handlers:
            handler.setFormatter(self.log_formatter)
            root.addHandler(handler)
    
    def init_request(self, environ):
        super(LoggingAppMixin, self).init_request(environ)
        self.log_formatter.init_request(environ)
    
    
    
    
    
    
    
    
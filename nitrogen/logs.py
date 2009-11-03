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
import time

thread_local = threading.local()


class setup_logging(object):
    """WSGI middleware that stores information about the request so that logs
    will contain the request id, and remote address.
    
    Currently stores the environment on environ, and a one-based request
    counter on request_index.
    
    """
    
    def __init__(self, app):
        self.app = app
        self.request_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        with self.lock:
            self.request_count += 1
            thread_local.request_index = self.request_count
            thread_local.remote_addr = environ['REMOTE_ADDR']
        return self.app(environ, start)


base_format = "%(asctime)s %(levelname)-8s pid:%(process)d req:%(request_index)d ip:%(remote_addr)s -- %(name)s: %(message)s"
class Formatter(logging.Formatter):
    def format(self, record):
        data = {
            'remote_addr': None,
            'request_index': 0,
            'process': 0,
            'asctime': 'DATETIME',
            'levelname': 'LEVELNAME',
            'message': 'MESSAGE'
        }
        data.update(thread_local.__dict__)
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
        

formatter = Formatter()


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
            self.fh = open(path, 'ab')
            os.chmod(path, 0777)
        self.last_path = path
        
        self.fh.write(self.format(record))
        self.fh.write('\n')
        self.fh.flush()



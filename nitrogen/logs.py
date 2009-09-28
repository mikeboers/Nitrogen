"""Logging module.

There are functions in here to setup the main methods of logging. The example
webapp runs them during it's setup procedure.

There is a log_extra_filler in middlewear to fill in the IP and thread_i onto
the "extra" object so they will be in the logs.

"""

import os
import sys
import logging
import logging.handlers
import threading
import time

from . import config

# This object will be used to populate all of the logging records.
# There is middlewear that sets the attributes on this object.
extra = threading.local()

base_format = "%(asctime)s %(levelname)-8s pid:%(process)d req:%(thread_i)d ip:%(ip)s -- %(name)s: %(message)s"
class Formatter(logging.Formatter):
    def format(self, record):
        data = {
            'ip': None,
            'thread_i': 0,
            'process': 0,
            'asctime': 'DATETIME',
            'levelname': 'LEVELNAME',
            'message': 'MESSAGE'
        }
        data.update(record.__dict__)
        data.update(extra.__dict__)
        
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
    """File log handler which writes out to a path aftet running it
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
            umask = os.umask(0113)
            self.fh = open(path, 'a')
            os.umask(umask)
        self.last_path = path
        
        self.fh.write(self.format(record))
        self.fh.write('\n')
        self.fh.flush()


_is_setup = False
def setup():
    global _is_setup
    if _is_setup:
        return
    root = logging.getLogger()
    root.setLevel(config.log_level)
    for handler in config.log_handlers:
        handler.setFormatter(formatter)
        root.addHandler(handler)
    _is_setup = True
    
    logger = logging.getLogger(__name__)
    logger.debug('Logs setup.')
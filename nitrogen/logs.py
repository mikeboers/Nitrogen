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

# This object will be used to populate all of the logging records.
# There (will) be middlewear that will set attributes on this object.
extra = threading.local()

root = logging.getLogger()

base_format = "%(asctime)s %(levelname)-8s pid:%(process)d req:%(thread_i)d ip:%(ip)s -- %(message)s"
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
        
        if '(asctime)' in base_format:
            data['asctime'] = self.formatTime(record)
        try:
            data['message'] = record.msg % record.args
        except:
            data['message'] = record.msg
        
        return base_format % data
formatter = Formatter()

def _setup():
    root.setLevel(logging.DEBUG)

def setup_stderr():
    _setup()
    
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(formatter)
    root.addHandler(stderr_handler)
     
def setup_timed_file(path_format):
    _setup()
    
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
    
    file_handler = FileHandler(path_format)
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)


    
def setup_smtp(args, level=logging.CRITICAL):
    _setup()
    email_handler = logging.handlers.SMTPHandler(*args)
    email_handler.setLevel(level)
    email_handler.setFormatter(formatter)
    root.addHandler(email_handler)


if __name__ == '__main__':
    setup()
    logging.debug('Message.')
    logging.info('Message.')
    logging.warning('Message.')
    logging.error('Message.')
    logging.critical('Message.')
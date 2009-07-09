import threading
import logging

from .. import logs

class log_extra_filler(object):
    def __init__(self, app):
        self.app = app
        self.thread_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        self.lock.acquire()
        self.thread_count += 1
        nitrogen.local.thread_i = self.thread_count
        self.lock.release()
        nitrogen.local.ip = environ.get('REMOTE_ADDR')
        return self.app(environ, start)
import threading

import nitrogen.logs as logs

class log_extra_filler(object):
    def __init__(self, app):
        self.app = app
        self.thread_count = 0
        self.lock = threading.Lock()

    def __call__(self, environ, start):
        if not hasattr(logs.extra, 'thread_i'):
            self.lock.acquire()
            self.thread_count += 1
            logs.extra.thread_i = self.thread_count
            self.lock.release()
        logs.extra.ip = environ.get('REMOTE_ADDR')
        return self.app(environ, start)
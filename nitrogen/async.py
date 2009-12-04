
import sys
from threading import Thread
from functools import partial


class NotFinished(Exception):
    pass


def call_async(func, *args, **kwargs):
    state = {}
    def thread_target():
        try:
            state['res'] = func(*args, **kwargs)
        except Exception as e:
            state['exc_info'] = sys.exc_info()
    thread = Thread(target=thread_target)
    thread.start()
    def get_result(join=True):
        if join:
            thread.join()
        if 'exc_info' in state:
            type_, value, tb = state['exc_info']
            raise type_, value, tb
        if 'res' not in state:
            raise NotFinished('call did not finish yet')
        return state['res']
    return get_result


if __name__ == '__main__':
    
    import time
    def example(delay):
        time.sleep(delay)
        return delay
    
    print 'here'
    get_res = call_async(example, 0.25)
    
    print 'doing something else'
    while True:
        try:
            print get_res(False)
            break
        except NotFinished:
            print 'not done'
            time.sleep(0.1)
            
    print 'done all'
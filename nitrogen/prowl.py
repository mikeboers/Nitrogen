"""Module for sending notifications to an iPhone via Prowl.

Currently I only support the send API method, and am having issues with the
verify method.

Note that, by default, the sync method will block until the request is complete.
If you set async=True, then it will start a thread to send the request. You may
also provide a callback which will be called with True/False indicating success.
In order to make sure that async messages are sent, an atexit function is
registered that waits for all of the threads to join. I didn't think I would
need to do that, but I get errors if I do not.

I can write something to disable that behaviour if it ends up being nasty, but
it seems sensible for now.

Also note that the server actually returns some XML that looks like this:
    <?xml version="1.0" encoding="UTF-8"?>
    <prowl>
    <success code="200" remaining="975" resetdate="1256310030" />
    </prowl>
I am currently ignoring all of this, and only looking for "success". The
remaning attribute is how many messages that will be accepted for this key until
the resetdate (unix timestamp) at which point the count will be reset (to 1000,
currently).

TODO:
    - test if I need the thread joining atexit function on a posix machine

See: http://prowl.weks.net/

"""

import urllib
import urllib2
import logging
from threading import Thread
import atexit

API_URL = 'https://prowl.weks.net/publicapi/%s'
DEFAULT_PRIORITY = 0
DEFAULT_APP = __name__
DEFAULT_EVENT = 'general'

_threads = set()

log = logging.getLogger(__name__)

def _wait_for_all_threads():
    if _threads:
        log.debug('waiting for prowl threads before exit')
    for thread in list(_threads):
        thread.join()

def verify(key):
    data = {'apikey': key}
    res = urllib2.urlopen(API_URL % 'verify', urllib.urlencode(data))
    print res.read()
    
def send(key, message, priority=None, app=None, event=None, async=False, callback=None):
    """Send a message.
    
    Parameters:
        key -- The API key for your device as given by the Prowl website.
        message -- The message to send.
        priority -- Integer from -2 to 2 inclusive.
        app -- App identifier to send as.
        event -- Event identifier to send as.
    """
    

    data = {
        'apikey': key,
        'priority': int(priority or DEFAULT_PRIORITY),
        'application': str(app or DEFAULT_APP)[:256],
        'event': str(event or DEFAULT_EVENT)[:1024],
        'description': str(message)[:10000]
    }
    thread = None
    def target():
        res = urllib2.urlopen(API_URL % 'add', urllib.urlencode(data))
        res_data = res.read()
        success = 'success' in res_data
        print res_data
        res.close()
        if async:
            _threads.remove(thread)
            if callback:
                callback(success)
        else:
            return success
    if async:
        if not send.setup_async:
            send.setup_async = True
            atexit.register(_wait_for_all_threads)
        thread = Thread(target=target)
        _threads.add(thread)
        thread.start()
    else:
        return target()
        
send.setup_async = False

class Prowl(object):
    """An object to simplify repeated prowling.
    
    Parameters for the constructor are the same as for prowl.send, and set the
    defaults which can be overidden by the Prowl.send (except for the key,
    that may never change.)
    """
    
    def __init__(self, key, priority=None, app=None, event=None, async=None):
        self.key = key
        self.priority = priority
        self.app = app
        self.event = event
        self.async = async
    
    def send(self, message, priority=None, app=None, event=None, async=None):
        """Send a message.
        
        Parameters here overide the defaults of this object.
        """
        return send(
            key=self.key,
            message=message,
            priority=priority or self.priority,
            app=app or self.app,
            event=event or self.event,
            async=async if async is not None else self.async
        )

class LogHandler(logging.Handler, Prowl):
    """Log handler which sends messages via Prowl.
    
    Constructor takes prowl parameters which will be used when sending logs.
    """
    
    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self)
        Prowl.__init__(self, *args, **kwargs)

    def emit(self, record):
        msg = self.format(record)
        self.send(msg, self.priority, self.app, self.event)

if __name__ == '__main__':
    import time
    KEY = '8e1bd6fef4e1d49aa1a8e6ad9d47abdbdecb1ff7'
    send(KEY, 'This is a message', async=True)
    exit()
    # prowler = Prowl('8e1bd6fef4e1d49aa1a8e6ad9d47abdbdecb1ff7',
    #     event='Testing'
    # )
    # assert prowler.send("This is a test!"), 'Did not send!'
    handler = LogHandler('8e1bd6fef4e1d49aa1a8e6ad9d47abdbdecb1ff7')
    logger = logging.getLogger(__name__ + '.test')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.info("This is info!")
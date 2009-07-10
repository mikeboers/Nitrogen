"""Module for sending notifications to an iPhone via Prowl.

See: http://prowl.weks.net/
"""

import urllib
import urllib2
import logging

API_URL = 'https://prowl.weks.net/publicapi/add'
DEFAULT_PRIORITY = 0
DEFAULT_APP = 'Python'
DEFAULT_EVENT = 'Event'

def send(key, message, priority=None, app=None, event=None):
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
    req = urllib2.urlopen(API_URL, urllib.urlencode(data))
    return 'success' in req.read()

class Prowl(object):
    """An object to simplify repeated prowling.
    
    Parameters for the constructor are the same as for prowl.send, and set the
    defaults which can be overidden by the Prowl.send (except for the key,
    that may never change.)
    """
    
    def __init__(self, key, priority=None, app=None, event=None):
        self.key = key
        self.priority = priority
        self.app = app
        self.event = event
    
    def send(self, message, priority=None, app=None, event=None):
        """Send a message.
        
        Parameters here overide the defaults of this object.
        """
        return send(self.key, message, priority or self.priority, app or self.app, event or self.event)

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
    # prowler = Prowl('8e1bd6fef4e1d49aa1a8e6ad9d47abdbdecb1ff7',
    #     event='Testing'
    # )
    # assert prowler.send("This is a test!"), 'Did not send!'
    handler = LogHandler('8e1bd6fef4e1d49aa1a8e6ad9d47abdbdecb1ff7')
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    logging.info("This is info!")
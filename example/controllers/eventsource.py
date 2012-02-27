#!../../bin/python2.6


import sys
import time
import logging
import cgi
import datetime
import logging
import struct
import hashlib
import json
import os

from nitrogen.eventsource import event

from . import *

log = logging.getLogger(__name__)


@route('/')
def do_index(request):
    return Response('''<html>
<head>
    <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/themes/smoothness/jquery-ui.css" type="text/css" media="screen">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js"></script>
    <script>jQuery(function($) {
        var log = function(x) { $('#log').append($('<li/>').text(x)); }
        log('start of log');
        
        var source = new EventSource('/eventsource/source')
            
        source.addEventListener('message', function(e) {
            log('"' + e.data + '"');
        }, false);

        source.addEventListener('open', function(e) {
          // Connection was opened.
          log('open')
        }, false);

        source.addEventListener('error', function(e) {
          if (e.eventPhase == EventSource.CLOSED) {
            // Connection was closed.
            source.close();
            log('closed')
          }
        }, false);


    })
    </script>
</head><body>

<h1>EventSource Test</h1>
<pre><ul id="log"></ul></pre>
    
''')
    

counter = 0

@route('/source')
def do_iframe(request):
    def _events():
        global counter
        
        # for name, value in sorted(environ.iteritems()):
        #     if name.startswith('HTTP'):
        #         yield event('%s: %r' % (name, value))
        # yield event('trailing\n')
        # yield event('before\nafter')
        # yield event(' leading\n spaces')
        # yield event(json.dumps(dict(key='value')))

        count = counter
        counter += 1
        
        for i in range(10):
            yield event('ping %d-%d' % (count, i), id=i)
            time.sleep(1)

    return Response(_events(), mimetype='text/event-stream')







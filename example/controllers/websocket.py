#!../../bin/python2.6


import sys
import time
import logging
import cgi
import datetime
import logging
import struct
import hashlib
from socket import error as socket_error
import json

import gevent
from gunicorn.workers.async import ALREADY_HANDLED

from nitrogen import websocket

from . import *

from nitrogen import status

log = logging.getLogger(__name__)





@route('/')
def do_index(request):
    return Response('''<html>
<head>
    <link rel="icon" href="/favicon.png" type="image/png">
    <link rel="stylesheet" href="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/themes/smoothness/jquery-ui.css" type="text/css" media="screen">
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.6.2/jquery.min.js"></script>
    <script src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.16/jquery-ui.min.js"></script>
    <script>jQuery(function($) {
    
        var log = function(x) { $('#log').append($('<li/>').text(x)); }
        if (window.MozWebSocket) {
            window.WebSocket = MozWebSocket;
        }
        
        ws = new WebSocket('ws://%s/websocket/socket');
        console.log('SOCKET', ws);
        
        ws.onopen = function(e) { log('OPEN'); ws.send('ready')};
        ws.onerror = function(e) { log('ERROR'); console.log('ERROR', e) };
        ws.onclose = function(e) { log('CLOSED'); console.log('CLOSED', e) };
        ws.onmessage = function(e) { log('RECV: ' + e.data); console.log('MESSAGE', e) };
                
        $input = $('input[type=text]');
        $('form').submit(function() {
            log('SEND: ' + $input.val());
            try {
                ws.send($input.val());
            } catch (e) {
                console.log(e);
                log('exception while sending');
            }
            $input.val('');
            return false;
        })
        
    })
    </script>
</head><body>

<h1>WebSocket Test</h1>
<ul id="log"></ul>

<form>
    <input type="text" />
    <input type="submit" />
</form>

''' % request.host)
    


@route('/socket')
def do_socket(request):
    
    if not request.is_websocket:
        raise status.BadRequest('must be websocket')
    
    def _do_socket(socket):
        socket.send('server started')
        
        socket.send(json.dumps(dict(request.cookies)))
        
        def _ping():
            while True:
                time.sleep(60)
                try:
                    socket.send('ping!')
                except websocket.Error:
                    break
        
        def _env():
            for k, v in sorted(socket.environ.iteritems()):
                time.sleep(1)
                try:
                    socket.send('%s: %r' % (k, v))
                except websocket.Error:
                    break
        
        def _echo():
            while True:
                msg = socket.recv()
                if not msg:
                    break
                socket.send(msg[::-1])
        
        tasks = [gevent.spawn(_ping), gevent.spawn(_echo)]
        for task in tasks:
            task.join()
            
    return websocket.Response(_do_socket)




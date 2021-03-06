"""

Originally lifted from various files at:
https://bitbucket.org/Jeffrey/gevent-websocket/src/fabf03111c73/geventwebsocket


"""

from errno import EINTR
from hashlib import md5, sha1
from socket import error as socket_error
from threading import Semaphore
from urllib import quote
import base64
import re
import struct
import sys
import logging
import itertools

import werkzeug as wz
import werkzeug.utils

from . import request
from . import status


log = logging.getLogger(__name__)


def patch(cls):
    def _patcher(func):
        old_func = getattr(cls, func.__name__)
        def _patch(*args, **kwargs):
            return func(old_func, *args, **kwargs)
        setattr(cls, func.__name__, _patch)
        return _patch
    return _patcher

try:
    import gunicorn.http.wsgi
except ImportError:
    pass
else:
    
    @patch(gunicorn.http.wsgi.Response)
    def __init__(old, self, *args, **kwargs):
        old(self, *args, **kwargs)
        self.websocket = False
    
    @patch(gunicorn.http.wsgi.Response)
    def start_response(old, self, *args):
        write = old(self, *args)
        if self.websocket:
            self.send_headers()
        return write

    @patch(gunicorn.http.wsgi.Response)
    def process_headers(old, self, headers):
        # Check if this is a websocket response.
        for name, value in headers:
            if name.strip().lower() == 'upgrade' and value.strip().lower() == 'websocket':
                self.websocket = True
                break
        old(self, headers)
        # The old function filters out all hoppish headers, but leaves in
        # "Connection: Upgrade" for us. We need to manually re-add the "Upgrade"
        # header for WebSockets.
        if self.websocket:
            # The case of "websocket" *may* matter, but I'm not sure.
            self.headers.append(('Upgrade', 'WebSocket'))
            
    @patch(gunicorn.http.wsgi.Response)
    def default_headers(old, self):
        headers = old(self)
        # If we are a websocket we have our own connection header to send.
        if self.websocket:
            headers = [x for x in headers if not x.lower().startswith('connection')]
        return headers

    @patch(gunicorn.http.wsgi.Response)
    def is_chunked(old, self):
        # WebSockets are not chunked, but the default logic will treat them as such.
        if self.websocket:
            return False
        return old(self)


if sys.version_info[:2] == (2, 7):
    # Python 2.7 has a working BufferedReader but socket.makefile() does not
    # use it.
    # Python 2.6's BufferedReader is broken (TypeError: recv_into() argument
    # 1 must be pinned buffer, not bytearray).
    from io import BufferedReader, RawIOBase

    class SocketIO(RawIOBase):
        def __init__(self, sock):
            RawIOBase.__init__(self)
            self._sock = sock

        def readinto(self, b):
            self._checkClosed()
            while True:
                try:
                    return self._sock.recv_into(b)
                except socket_error as ex:
                    if ex.args[0] == EINTR:
                        continue
                    raise

        def readable(self):
            return self._sock is not None

        @property
        def closed(self):
            return self._sock is None

        def fileno(self):
            self._checkClosed()
            return self._sock.fileno()

        @property
        def name(self):
            if not self.closed:
                return self.fileno()
            else:
                return -1

        def close(self):
            if self._sock is None:
                return
            else:
                self._sock.close()
                self._sock = None
                RawIOBase.close(self)

    def makefile(socket):
        return BufferedReader(SocketIO(socket))

else:
    def makefile(socket):
        # XXX on python3 enable buffering
        return socket.makefile()


if sys.version_info[:2] < (2, 7):
    def is_closed(fobj):
        return fobj._sock is None
else:
    def is_closed(fobj):
        return fobj.closed


class Error(socket_error):
    pass


class FrameTooLargeException(Error):
    pass



class Response(request.Response):
    """A WebSocket response.
    
    Not reuseable!
    
    """
    
    GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    SUPPORTED_VERSIONS = ('13', '8', '7')
    
    def run(self):
        return self.application(self.websocket)
    
    def __init__(self, app):
        self.application = app
        super(Response, self).__init__(direct_passthrough=True)
    
    def __call__(self, environ, start_response):
        
        self.environ = environ
        self.start_response = start_response
        
        # Make sure it is a websocket.
        upgrade = environ.get('HTTP_UPGRADE', '').strip().lower()
        connection = environ.get('HTTP_CONNECTION', '').strip().lower()
        if connection != 'upgrade' or upgrade != 'websocket':
            raise ValueError('request not for websocket')
        
        # Get the raw socket: this depends on the server.
        if 'gunicorn.socket' in environ:
            self.socket = environ['gunicorn.socket']
        else:
            raise ValueError('no socket')
        
        # Dispatch to the right version.
        if environ.get("HTTP_SEC_WEBSOCKET_VERSION"):
            do_run_app = self._handle_hybi()
        elif environ.get("HTTP_ORIGIN"):
            do_run_app = self._handle_hixie()
        else:
            self.client_error('could not determine websocket version')
            do_run_app = False
        
        headers = [(n, v) for n, v in self.headers if n.lower() != 'content-length']
        write = self.start_response(self.status, headers)
        
        if do_run_app:
            return itertools.chain(self.response, self.run() or [])
        else:
            return self.response

    def client_error(self, msg, status='400 Bad Request', headers=[]):
        self.status = status
        self.headers.extend(headers)
        log.warning(msg)
    
    def _handle_hybi(self):
        environ = self.environ
        version = environ.get("HTTP_SEC_WEBSOCKET_VERSION")

        self.version = environ['wsgi.websocket_version'] = 'hybi-%s' % version

        if version not in self.SUPPORTED_VERSIONS:
            self.client_error(
                'unsupported version: %r' % version,
                '400 Unsupported Version',
                [('Sec-WebSocket-Version', ', '.join(self.SUPPORTED_VERSIONS))]
            )
            return

        protocol, version = environ['SERVER_PROTOCOL'].split("/")
        key = environ.get("HTTP_SEC_WEBSOCKET_KEY")

        # check client handshake for validity
        if not environ.get("REQUEST_METHOD") == "GET": # 5.2.1 (1)
            self.client_error('must be GET')
            return
        elif not protocol == "HTTP": # 5.2.1 (1)
            self.client_error('must be HTTP')
            return
        elif float(version) < 1.1: # 5.2.1 (1)
            self.client_error('must be HTTP/1.1')
            return
        elif not key: # 5.2.1 (3)
            self.client_error('Sec-WebSocket-Key is missing')
            return
        elif len(base64.b64decode(key)) != 16: # 5.2.1 (3)
            self.client_error('invalid Sec-WebSocket-Key')
            return

        self.websocket = WebSocketHybi(self.socket, environ)
                
        self.status = "101 Switching Protocols"
        self.headers.extend([
            ("Upgrade", "websocket"),
            ("Connection", "Upgrade"),
            ("Sec-WebSocket-Accept", base64.b64encode(sha1(key + self.GUID).digest())),
        ])
        
        return True

    def _handle_hixie(self):

        key1 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY1')
        key2 = self.environ.get('HTTP_SEC_WEBSOCKET_KEY2')

        if key1 is not None:
            self.version = environ['wsgi.websocket_version'] = 'hixie-76'
            if not key1:
                self.client_error('Sec-WebSocket-Key1 is missing')
                return
            if not key2:
                self.client_error('Sec-WebSocket-Key2 is missing')
                return

            part1 = self._get_hixie_key_value(key1)
            part2 = self._get_hixie_key_value(key2)
            if part1 is None or part2 is None:
                self.client_error('invalid websocket keys')
                return

        self.websocket = WebSocketHixie(self.socket, environ)
        self.status = "101 Web Socket Protocol Handshake"
        self.headers.extend([
            ("Upgrade", "WebSocket"),
            ("Connection", "Upgrade"),
            ("Sec-WebSocket-Location", reconstruct_url(environ)),
        ])
        if self.websocket.protocol is not None:
            self.headers.append(("Sec-WebSocket-Protocol", self.websocket.protocol))
        if self.websocket.origin:
            self.headers.append(("Sec-WebSocket-Origin", self.websocket.origin))

        if key1 is not None:
            
            # This request should have 8 bytes of data in the body
            key3 = self.rfile.read(8)
            challenge = md5(struct.pack("!II", part1, part2) + key3).digest()
            
            # TODO this must be delayed, or it will fail.
            self.response = [self.socket.sendall(challenge)]
            
        return True
    
    def _get_hixie_key_value(self, key_value):
        key_number = int(re.sub("\\D", "", key_value))
        spaces = re.subn(" ", "", key_value)[1]

        if key_number % spaces != 0:
            self.log_error("key_number %d is not an intergral multiple of spaces %d", key_number, spaces)
        else:
            return key_number / spaces


def reconstruct_url(environ):
    secure = environ['wsgi.url_scheme'] == 'https'
    if secure:
        url = 'wss://'
    else:
        url = 'ws://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

        if secure:
            if environ['SERVER_PORT'] != '443':
                url += ':' + environ['SERVER_PORT']
        else:
            if environ['SERVER_PORT'] != '80':
                url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME', ''))
    url += quote(environ.get('PATH_INFO', ''))

    if environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']

    return url


class WebSocket(object):
    def _encode_text(self, text):
        if isinstance(text, unicode):
            return text.encode('utf-8')
        else:
            return text


class WebSocketHixie(WebSocket):
    def __init__(self, socket, environ):
        self.environ = environ
        self._fobj = socket.makefile()
        self._writelock = Semaphore(1)
        self._write = socket.sendall

    @wz.utils.cached_property
    def origin(self):
        return self.environ.get("HTTP_ORIGIN")
    
    @wz.utils.cached_property
    def protocol(self):
        return self.environ.get("HTTP_SEC_WEBSOCKET_PROTOCOL")
    
    def send(self, message):
        message = self._encode_text(message)
        with self._writelock:
            self._write("\x00" + message + "\xFF")

    def close(self):
        if self._fobj is not None:
            # dono't actually close it
            # self._fobj.close()
            self._fobj = None
            self._write = None

    def _message_length(self):
        length = 0

        while True:
            if self._fobj is None:
                raise Error('Connection closed unexpectedly while reading message length')
            byte_str = self._fobj.read(1)

            if not byte_str:
                return 0
            else:
                byte = ord(byte_str)

            if byte != 0x00:
                length = length * 128 + (byte & 0x7f)
                if (byte & 0x80) != 0x80:
                    break

        return length

    def _read_until(self):
        bytes = []

        read = self._fobj.read

        while True:
            if self._fobj is None:
                msg = ''.join(bytes)
                raise Error('Connection closed unexpectedly while reading message: %r' % msg)

            byte = read(1)
            if ord(byte) != 0xff:
                bytes.append(byte)
            else:
                break

        return ''.join(bytes)

    def recv(self):
        read = self._fobj.read

        while self._fobj is not None:
            frame_str = read(1)

            if not frame_str:
                self.close()
                return
            else:
                frame_type = ord(frame_str)

            if frame_type == 0x00:
                bytes = self._read_until()
                return bytes.decode("utf-8", "replace")
            else:
                raise Error("Received an invalid frame_type=%r" % frame_type)


class WebSocketHybi(WebSocket):
    OPCODE_TEXT = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CLOSE = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xA

    def __init__(self, socket, environ):
        self.environ = environ
        self._chunks = bytearray()
        self._writelock = Semaphore(1)
        self._socket = socket
        self._write = socket.sendall
        self._fobj = makefile(socket)
        self._close_code = None
        self._close_message = None
        self._reading = False

    @wz.utils.cached_property
    def origin(self):
        return self.environ.get("HTTP_SEC_WEBSOCKET_ORIGIN")

    @wz.utils.cached_property
    def protocol(self):
        return self.environ.get("HTTP_SEC_WEBSOCKET_PROTOCOL", 'unknown')

    def _parse_header(self, data):
        if len(data) != 2:
            self._close()
            raise Error('Incomplete read while reading header: %r' % data)

        first_byte, second_byte = struct.unpack('!BB', data)

        fin = (first_byte >> 7) & 1
        rsv1 = (first_byte >> 6) & 1
        rsv2 = (first_byte >> 5) & 1
        rsv3 = (first_byte >> 4) & 1
        opcode = first_byte & 0xf

        # frame-fin = %x0 ; more frames of this message follow
        #           / %x1 ; final frame of this message

        # frame-rsv1 = %x0 ; 1 bit, MUST be 0 unless negotiated otherwise
        # frame-rsv2 = %x0 ; 1 bit, MUST be 0 unless negotiated otherwise
        # frame-rsv3 = %x0 ; 1 bit, MUST be 0 unless negotiated otherwise
        if rsv1 or rsv2 or rsv3:
            self.close(1002)
            raise Error('Received frame with non-zero reserved bits: %r' % str(data))

        if opcode > 0x7 and fin == 0:
            self.close(1002)
            raise Error('Received fragmented control frame: %r' % str(data))

        if len(self._chunks) > 0 and fin == 0 and not opcode:
            self.close(1002)
            raise Error('Received new fragment frame with non-zero opcode: %r' % str(data))

        if len(self._chunks) > 0 and fin == 1 and (self.OPCODE_TEXT <= opcode <= self.OPCODE_BINARY):
            self.close(1002)
            raise Error('Received new unfragmented data frame during fragmented message: %r' % str(data))

        has_mask = (second_byte >> 7) & 1
        length = (second_byte) & 0x7f

        # Control frames MUST have a payload length of 125 bytes or less
        if opcode > 0x7 and length > 125:
            self.close(1002)
            raise FrameTooLargeException("Control frame payload cannot be larger than 125 bytes: %r" % str(data))

        return fin, opcode, has_mask, length

    def recv_frame(self):
        """Return the next frame from the socket."""
        fobj = self._fobj

        if fobj is None:
            return

        if is_closed(fobj):
            return

        read = self._fobj.read

        assert not self._reading, 'Reading is not possible from multiple greenlets'
        self._reading = True

        try:
            data0 = read(2)

            if not data0:
                self._close()
                return

            fin, opcode, has_mask, length = self._parse_header(data0)

            if not has_mask and length:
                self.close(1002)
                raise Error('Message from client is not masked')

            if length < 126:
                data1 = ''
            elif length == 126:
                data1 = read(2)

                if len(data1) != 2:
                    self.close()
                    raise Error('Incomplete read while reading 2-byte length: %r' % (data0 + data1))

                length = struct.unpack('!H', data1)[0]
            else:
                assert length == 127, length
                data1 = read(8)

                if len(data1) != 8:
                    self.close()
                    raise Error('Incomplete read while reading 8-byte length: %r' % (data0 + data1))

                length = struct.unpack('!Q', data1)[0]

            mask = read(4)
            if len(mask) != 4:
                self._close()
                raise Error('Incomplete read while reading mask: %r' % (data0 + data1 + mask))

            mask = struct.unpack('!BBBB', mask)

            if length:
                payload = read(length)
                if len(payload) != length:
                    self._close()
                    args = (length, len(payload))
                    raise Error('Incomplete read: expected message of %s bytes, got %s bytes' % args)
            else:
                payload = ''

            if payload:
                payload = bytearray(payload)

                for i in xrange(len(payload)):
                    payload[i] = payload[i] ^ mask[i % 4]

            return fin, opcode, payload
        finally:
            self._reading = False
            if self._fobj is None:
                fobj.close()

    def _recv(self):
        """Return the next text or binary message from the socket."""

        opcode = None
        result = bytearray()

        while True:
            frame = self.recv_frame()
            if frame is None:
                if result:
                    raise Error('Peer closed connection unexpectedly')
                return

            f_fin, f_opcode, f_payload = frame

            if f_opcode in (self.OPCODE_TEXT, self.OPCODE_BINARY):
                if opcode is None:
                    opcode = f_opcode
                else:
                    raise Error('The opcode in non-fin frame is expected to be zero, got %r' % (f_opcode, ))
            elif not f_opcode:
                if opcode is None:
                    self.close(1002)
                    raise Error('Unexpected frame with opcode=0')
            elif f_opcode == self.OPCODE_CLOSE:
                if len(f_payload) >= 2:
                    self._close_code = struct.unpack('!H', str(f_payload[:2]))[0]
                    self._close_message = f_payload[2:]
                elif f_payload:
                    self._close()
                    raise Error('Invalid close frame: %s %s %s' % (f_fin, f_opcode, repr(f_payload)))
                code = self._close_code
                if code is None or (code >= 1000 and code < 5000):
                    self.close()
                else:
                    self.close(1002)
                    raise Error('Received invalid close frame: %r %r' % (code, self._close_message))
                return
            elif f_opcode == self.OPCODE_PING:
                self.send_frame(f_payload, opcode=self.OPCODE_PONG)
                continue
            elif f_opcode == self.OPCODE_PONG:
                continue
            else:
                self._close()  # XXX should send proper reason?
                raise Error("Unexpected opcode=%r" % (f_opcode, ))

            result.extend(f_payload)
            if f_fin:
                break

        if opcode == self.OPCODE_TEXT:
            return result, False
        elif opcode == self.OPCODE_BINARY:
            return result, True
        else:
            raise AssertionError('internal serror in gevent-websocket: opcode=%r' % (opcode, ))

    def recv(self):
        result = self._recv()
        if not result:
            return result

        message, is_binary = result
        if is_binary:
            return message
        else:
            try:
                return message.decode('utf-8')
            except ValueError:
                self.close(1007)
                raise

    def send_frame(self, message, opcode):
        """Send a frame over the websocket with message as its payload"""

        if self._socket is None:
            raise Error('The connection was closed')

        header = chr(0x80 | opcode)

        if isinstance(message, unicode):
            message = message.encode('utf-8')

        msg_length = len(message)

        if msg_length < 126:
            header += chr(msg_length)
        elif msg_length < (1 << 16):
            header += chr(126) + struct.pack('!H', msg_length)
        elif msg_length < (1 << 63):
            header += chr(127) + struct.pack('!Q', msg_length)
        else:
            raise FrameTooLargeException()

        try:
            combined = header + message
        except TypeError:
            with self._writelock:
                self._write(header)
                self._write(message)
        else:
            with self._writelock:
                self._write(combined)

    def send(self, message, binary=None):
        """Send a frame over the websocket with message as its payload"""
        if binary is None:
            binary = not isinstance(message, (str, unicode))

        if binary:
            return self.send_frame(message, self.OPCODE_BINARY)
        else:
            return self.send_frame(message, self.OPCODE_TEXT)

    def close(self, code=1000, message=''):
        """Close the websocket, sending the specified code and message"""
        if self._socket is not None:
            message = self._encode_text(message)
            self.send_frame(struct.pack('!H%ds' % len(message), code, message), opcode=self.OPCODE_CLOSE)
            self._close()

    def _close(self):
        if self._socket is not None:
            self._socket = None
            self._write = None

            if not self._reading:
                pass
                # don't actually close
                # self._fobj.close()

            self._fobj = None






        
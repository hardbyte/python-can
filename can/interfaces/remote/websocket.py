import base64
import hashlib
import logging
import random
import select
import socket
import struct
import sys
import threading
try:
    from http.client import HTTPConnection, HTTPSConnection
    from urllib.parse import urlparse
except ImportError:
    from httplib import HTTPConnection, HTTPSConnection
    from urlparse import urlparse

import can


LOGGER = logging.getLogger(__name__)

STREAM = 0x0
TEXT = 0x1
BINARY = 0x2
CLOSE = 0x8
PING = 0x9
PONG = 0xA


def get_accept_key(key):
    k = key.encode('ascii') + b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    return base64.b64encode(hashlib.sha1(k).digest()).decode()


class WebSocket(object):
    """A WebSocket connection.

    Only for internal use!
    """

    def __init__(self, url, protocols=None, headers=None, sock=None):
        """
        :param str url:
            URL to server
        :param list protocols:
            List of requested protocols from client
        :param dict headers:
            Additional headers to send to server
        :param socket.socket sock:
            An already established socket by a server
        """
        self.url = url
        self.protocol = protocols
        self.socket = sock
        # Use masking if we are a WebSocket client
        self.mask = sock is None
        self.closed = False
        self._send_lock = threading.Lock()
        if sock is None:
            self.connect(protocols, headers)

    def connect(self, protocols, headers=None):
        o = urlparse(self.url, scheme="ws")
        if o.scheme == "wss":
            conn = HTTPSConnection(o.netloc)
        else:
            conn = HTTPConnection(o.netloc)
        if headers is None:
            headers = {}
        rand = bytes(random.getrandbits(8) for _ in range(16))
        key = base64.b64encode(rand).decode()
        headers["User-Agent"] = "python-can/%s (%s)" % (
            can.__version__, sys.platform)
        headers["Upgrade"] = "WebSocket"
        headers["Connection"] = "Upgrade"
        headers["Sec-WebSocket-Key"] = key
        headers["Sec-WebSocket-Version"] = "13"
        if protocols:
            headers["Sec-WebSocket-Protocol"] = ",".join(protocols)
        conn.request("GET", o.path, headers=headers)
        res = conn.getresponse()
        LOGGER.debug("Server response headers:\n%s", res.getheaders())
        self.protocol = res.getheader("Sec-WebSocket-Protocol")
        self.socket = conn.sock

    def _read_exactly(self, n):
        buf = bytearray(n)
        view = memoryview(buf)
        nread = 0
        while nread < n:
            received = self.socket.recv_into(view[nread:])
            if received == 0:
                raise WebsocketClosed(1006, "Socket closed unexpectedly")
            nread += received
        return buf

    def wait(self, timeout=None):
        """Wait for data to be available on the socket."""
        return len(select.select([self.socket], [], [], timeout)[0]) > 0

    def read_frame(self):
        b1, b2 = self._read_exactly(2)
        opcode = b1 & 0xF
        mask_used = b2 & 0x80
        length = b2 & 0x7F
        if length == 126:
            length, = struct.unpack(">H", self._read_exactly(2))
        elif length == 127:
            length, = struct.unpack(">Q", self._read_exactly(8))
        if mask_used:
            mask = self._read_exactly(4)
        data = self._read_exactly(length)
        if mask_used:
            for i, b in enumerate(data):
                data[i] = b ^ mask[i % 4]
        return opcode, data

    def send_frame(self, opcode, data):
        length = len(data)
        payload = bytearray(2)
        payload[0] = opcode | 0x80
        if length <= 125:
            payload[1] = length
        elif length <= 65535:
            payload[1] = 126
            payload.extend(struct.pack(">H", length))
        else:
            payload[1] = 127
            payload.extend(struct.pack(">Q", length))
        if self.mask:
            mask = [random.getrandbits(8) for _ in range(4)]
            payload[1] |= 0x80
            payload.extend(mask)
            for i, b in enumerate(data):
                if not isinstance(b, int):
                    # If Python 2.7
                    b = ord(b)
                payload.append(b ^ mask[i % 4])
        else:
            payload.extend(data)
        with self._send_lock:
            if not self.closed:
                self.socket.sendall(payload)

    def read(self):
        """Read next message

        :return:
            A string or bytearray depending on if it is a binary or text message
        """
        while True:
            opcode, data = self.read_frame()
            if opcode == TEXT:
                return data.decode("utf-8")
            elif opcode == BINARY:
                return data
            elif opcode == PING:
                LOGGER.debug("PING")
                self.send_frame(PONG, data)
            elif opcode == CLOSE:
                if not data:
                    self.close()
                    raise WebsocketClosed(1000, "")
                else:
                    status, = struct.unpack_from(">H", data)
                    reason = data[2:].decode("utf-8")
                    self.close(status, reason)
                    raise WebsocketClosed(status, reason)

    def send(self, obj):
        """Send a message.

        :param obj:
            A binary or text object to send
        :type obj: str, bytearray
        """
        if isinstance(obj, bytearray):
            self.send_frame(BINARY, obj)
        else:
            self.send_frame(TEXT, obj.encode("utf-8"))

    def close(self, status=1000, reason=""):
        """Close connection."""
        if not self.closed:
            try:
                payload = struct.pack(">H", status) + reason.encode("utf-8")
                self.send_frame(CLOSE, payload)
            finally:
                with self._send_lock:
                    self.socket.shutdown(socket.SHUT_WR)
                    self.closed = True


class WebsocketClosed(Exception):
    """Websocket was closed either gracefully or unexpectedly."""

    def __init__(self, code, reason):
        self.code = code
        self.reason = reason

    def __str__(self):
        return "Status: %d, reason: %s" % (self.code, self.reason)

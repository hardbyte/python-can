import logging
import mimetypes
import os.path
import shutil
import threading
try:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    from socketserver import ThreadingMixIn
except ImportError:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
    from SocketServer import ThreadingMixIn

import can
from can.interfaces.remote import DEFAULT_PORT
from .protocol import RemoteProtocolBase
from .websocket import WebSocket, WebsocketClosed, get_accept_key


logger = logging.getLogger(__name__)


def create_connection(url, config=None):
    if config is None:
        config = {}
    headers = {"X-Can-Role": "server"}
    websocket = WebSocket(url, ["can.binary+json.v1", "can.json.v1"], headers=headers)
    protocol = RemoteServerProtocol(config, websocket)
    protocol.run()


class RemoteServer(ThreadingMixIn, HTTPServer):
    """Server for CAN communication."""

    daemon_threads = True

    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT, **config):
        """
        :param str host:
            Address to listen to.
        :param int port:
            Network port to listen to.
        :param channel:
            The can interface identifier. Expected type is backend dependent.
        :param str bustype:
            CAN interface to use.
        :param int bitrate:
            Forced bitrate in bits/s.
        """
        address = (host, port)
        self.config = config
        #: List of :class:`can.interfaces.remote.server.ClientRequestHandler`
        #: instances
        self.clients = []
        HTTPServer.__init__(self, address, ClientRequestHandler)
        logger.info("Server listening on %s:%d", address[0], address[1])
        logger.info("Connect using channel 'ws://localhost:%d/'",
                    self.server_port)
        logger.info("Open browser to 'http://localhost:%d/'", self.server_port)


class ClientRequestHandler(BaseHTTPRequestHandler):
    """A client connection on the server."""

    server_version = ("python-can/" + can.__version__ + " " +
                      BaseHTTPRequestHandler.server_version)

    protocol_version = "HTTP/1.1"

    disable_nagle_algorithm = True

    log_message = logger.debug

    def do_GET(self):
        if self.headers.get("Upgrade", "").lower() == "websocket":
            self.start_websocket()
        else:
            self.send_trace_webpage()

    def start_websocket(self):
        logger.info("Got connection from %s", self.address_string())
        self.send_response(101)
        self.send_header("Upgrade", "WebSocket")
        self.send_header("Connection", "Upgrade")
        self.send_header("Sec-WebSocket-Accept",
                         get_accept_key(self.headers["Sec-WebSocket-Key"]))
        protocols = self.headers.get("Sec-WebSocket-Protocol", "can.json.v1")
        protocols = [p.strip() for p in protocols.split(",")]
        protocol = "can.binary+json.v1" if "can.binary+json.v1" in protocols else "can.json.v1"
        self.send_header("Sec-WebSocket-Protocol", protocol)
        self.end_headers()

        websocket = WebSocket(None, protocol, sock=self.request)
        protocol = RemoteServerProtocol(self.server.config, websocket)
        self.server.clients.append(protocol)
        protocol.run()
        logger.info("Closing connection to %s", self.address_string())
        # Remove itself from the server's list of clients
        self.server.clients.remove(protocol)

    def send_trace_webpage(self):
        path = os.path.join(os.path.dirname(__file__), "web", self.path[1:])
        if path.endswith("/"):
            path = path + "index.html"
        # Prefer compressed files
        if os.path.exists(path + ".gz"):
            path = path + ".gz"
        if not os.path.exists(path):
            self.send_error(404)
            return
        self.send_response(200)
        type, encoding = mimetypes.guess_type(path, strict=False)
        if type:
            self.send_header("Content-Type", type)
        if encoding:
            self.send_header("Content-Encoding", encoding)
        self.send_header("Content-Length", str(os.path.getsize(path)))
        self.end_headers()
        with open(path, "rb") as infile:
            shutil.copyfileobj(infile, self.wfile)


class RemoteServerProtocol(RemoteProtocolBase):

    def __init__(self, config, websocket):
        super(RemoteServerProtocol, self).__init__(websocket)
        event = self.recv()
        if not event or event["type"] != "bus_request":
            print(event)
            raise RemoteServerError("Client did not send a bus request")
        new_config = {}
        new_config.update(event["payload"]["config"])
        logger.info("Config received: %r", new_config)
        new_config.update(config)
        self.config = new_config
        try:
            self.bus = can.interface.Bus(**new_config)
        except Exception as exc:
            self.terminate(exc)
            raise
        logger.info("Connected to bus '%s'", self.bus.channel_info)
        self.send_bus_response(self.bus.channel_info)
        self.running = True
        self._send_tasks = {}
        self._send_thread = threading.Thread(target=self._send_to_client)
        self._send_thread.daemon = True

    def send_bus_response(self, channel_info):
        self.send("bus_response", {"channel_info": channel_info})

    def run(self):
        self._send_thread.start()
        try:
            self._receive_from_client()
        except Exception as exc:
            self.terminate(exc)
        finally:
            self.running = False
            if self._send_thread.is_alive():
                self._send_thread.join(3)

    def _send_to_client(self):
        """Continuously read CAN messages and send to client."""
        while self.running:
            try:
                msg = self.bus.recv(0.5)
            except Exception as e:
                logger.exception(e)
                self.send_error(e)
            else:
                if msg is not None:
                    self.send_msg(msg)
        logger.info('Disconnecting from CAN bus')
        self.bus.shutdown()

    def _receive_from_client(self):
        """Continuously read events from socket and send messages on CAN bus."""
        while self.running:
            try:
                event = self.recv()
            except WebsocketClosed as exc:
                logger.info("Websocket closed: %s", exc)
                break
            if event is None:
                continue
            if isinstance(event, can.Message):
                self.bus.send(event)
            elif event["type"] == "periodic_start":
                msg = can.Message(**event["payload"]["msg"])
                arb_id = msg.arbitration_id
                if arb_id in self._send_tasks:
                    # Modify already existing task
                    self._send_tasks[arb_id].modify_data(msg)
                else:
                    # Create new task
                    task = self.bus.send_periodic(msg,
                                                  event["payload"]["period"],
                                                  event["payload"].get("duration"))
                    self._send_tasks[arb_id] = task
            elif event["type"] == "periodic_stop":
                self._send_tasks[event["payload"]].stop()


class RemoteServerError(Exception):
    pass


if __name__ == "__main__":
    RemoteServer(channel=0, bustype="virtual").serve_forever()

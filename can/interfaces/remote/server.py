import logging
import socket
import threading
import select
import can
#from can.interfaces import remote
from can.interfaces.remote import events
from can.interfaces.remote import connection


logger = logging.getLogger(__name__)


class RemoteServer(object):
    """Server for CAN communication."""

    def __init__(self, port=None, **config):
        """
        :param int port:
            Network port to listen to.
        :param channel:
            The can interface identifier. Expected type is backend dependent.
        :param str bustype:
            CAN interface to use.
        """
        self.port = port or can.interfaces.remote.DEFAULT_PORT
        self.config = config

        #: List of :class:`can.interfaces.remote.server.ClientBusConnection`
        #: instances
        self.clients = []

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start(self):
        """Start listening for incoming clients."""
        self.socket.bind(('', self.port))
        self.socket.listen(5)
        logger.info('Listening on port %d...', self.port)

        while True:
            try:
                conn, address = self.socket.accept()
            except KeyboardInterrupt:
                break

            logger.info('Got connection from %s', address)
            try:
                client = ClientBusConnection(conn, self)
            except RemoteServerError as e:
                logger.error(e)
                conn.close()
            else:
                self.clients.append(client)

        self.shutdown()

    def shutdown(self):
        self.socket.close()


class ClientBusConnection(object):
    """A client connection on the server."""

    def __init__(self, conn, server):
        """
        :param conn:
            A socket object to the client.
        :param server:
            The :class:`RemoteServer` object that received the connection.
        """
        #: Socket connection to client
        self.socket = conn
        self.server = server
        self.conn = connection.Connection()
        # Prevent threads to send data simultaneously
        self.lock = threading.Lock()
        self.stop_event = threading.Event()

        event = self._next_event()
        if isinstance(event, events.BusRequest):
            self._start_bus(event)
        elif isinstance(event, events.PeriodicMessageStart):
            self._start_periodic_transmit(event)
        else:
            raise RemoteServerError('Handshake error')

    def _start_bus(self, bus_event):
        #: Bitrate requested by client
        self.bitrate = bus_event.bitrate

        if bus_event.version != can.interfaces.remote.PROTOCOL_VERSION:
            raise RemoteServerError('Protocol version mismatch (%d != %d)' % (
                bus_event.version, can.interfaces.remote.PROTOCOL_VERSION))

        filter_event = self._next_event()
        if not isinstance(filter_event, events.FilterConfig):
            raise RemoteServerError('Handshake error')
        #: CAN filters requested by client
        self.can_filters = filter_event.can_filters

        #: A :class:`can.interface.Bus` object
        self.bus = can.interface.Bus(bitrate=self.bitrate,
                                     can_filters=self.can_filters,
                                     **self.server.config)
        logger.info("Connected to bus '%s'", self.bus.channel_info)
        self.conn.send_event(events.BusResponse(self.bus.channel_info))
        self.socket.sendall(self.conn.next_data())

        self.receive_thread = threading.Thread(
            target=self._receive_from_client, name='Receive from client')
        self.receive_thread.daemon = True
        self.receive_thread.start()
        self.send_thread = threading.Thread(target=self._send_to_client,
                                            name='Send to client')
        self.send_thread.daemon = True
        self.send_thread.start()

    def _start_periodic_transmit(self, start_event):
        #: Cyclic send task
        self.task = can.interface.CyclicSendTask(self.server.config['channel'],
                                                 start_event.msg,
                                                 start_event.period)

    def _next_event(self):
        """Block until a new event has been received.

        :return: Next event in queue
        """
        event = self.conn.next_event()
        while event is None:
            self.conn.receive_data(self.socket.recv(256))
            event = self.conn.next_event()
        return event

    def _next_event_from_bus(self, timeout=None):
        """Block until a new a CAN message is received or an exception occurrs.

        :return: An event
        """
        try:
            msg = self.bus.recv(timeout)
        except can.CanError as e:
            logger.error(e)
            return events.RemoteException(e)
        else:
            return None if msg is None else events.CanMessage(msg)

    def _receive_from_client(self):
        """Continuously read events from socket and send messages on CAN bus."""
        while not self.stop_event.is_set():
            event = self._next_event()
            if isinstance(event, events.CanMessage):
                self.send_msg(event.msg)
            elif isinstance(event, events.ConnectionClosed):
                break
            elif isinstance(event, events.PeriodicMessageStart):
                self.task.start()
            elif isinstance(event, events.PeriodicMessageStop):
                self.task.stop()
            elif isinstance(event, events.PeriodicMessageUpdate):
                self.task.modify_data(event.msg)

        logger.info('Closing connection to %s', self.socket.getpeername())
        # Remove itself from the server's list of clients
        self.server.clients.remove(self)
        self.stop_event.set()
        self.send_thread.join(1.0)
        with self.lock:
            self.socket.shutdown(socket.SHUT_WR)
            self.socket.close()
            self.socket = None

    def _send_to_client(self):
        """Continuously read CAN messages and send to client."""
        while not self.stop_event.is_set():
            # Wait for an event on CAN (max 0.5 seconds)
            event = self._next_event_from_bus(0.5)

            # Wait for client to be ready for new messages (max 0.5 seconds)
            select.select([], [self.socket], [], 0.5)

            # Read all CAN events to buffer
            while event is not None:
                self.conn.send_event(event)
                if isinstance(event, events.RemoteException):
                    # An exception while reading from CAN is probably a serious
                    # error so we stop everything
                    self.stop_event.set()
                    break
                event = self._next_event_from_bus(0)

            # Send all data at once if there is any
            data = self.conn.next_data()
            if data:
                self.socket.sendall(data)

        logger.info('Disconnecting from CAN bus')
        self.bus.shutdown()

    def send_msg(self, msg):
        """Send a CAN message to the bus."""
        try:
            self.bus.send(msg)
        except can.CanError as e:
            logger.error(str(e))
            self.conn.send_event(events.TransmitFail())


class RemoteServerError(Exception):
    pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    RemoteServer(bustype='kvaser', channel=0).start()

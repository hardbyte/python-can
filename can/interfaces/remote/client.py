import logging
import socket
import threading
try:
    import queue as queue
except ImportError:
    import Queue as queue
import can
from can.interfaces.remote import events
from can.interfaces.remote import connection


logger = logging.getLogger(__name__)


#: Max number of messages that can be buffered if `recv()` is not called
MAX_BUFFER_LENGTH = 16384


def create_connection(address):
    address = address.split(':')
    if len(address) >= 2:
        address = (address[0], int(address[1]))
    else:
        address = (address[0], can.interfaces.remote.DEFAULT_PORT)
    return socket.create_connection(address)


class RemoteBus(can.bus.BusABC):
    """CAN bus over a network connection bridge.

    A background thread is started to handle all incoming traffic from the
    server. Messages are placed in a queue which `recv()` reads from.
    Up to 16384 messages can be buffered until old messages are discarded.

    When `send()` is called, the message is transmitted directly to the server
    and then blocks until a confirmation has been received that the message
    was transmitted to the CAN bus successfully.
    """

    def __init__(self, channel, can_filters=None, **config):
        """
        :param str channel:
            Address of server as host:port (port may be omitted).

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            The filters are handed to the actual CAN interface on the server.

        :param int bitrate:
            Bitrate in bits/s to use on CAN bus. May be ignored by the interface.

        Any other backend specific configuration will be silently ignored.
        """
        # Event to stop background thread
        self.stop_event = threading.Event()
        # Condition for when a message has been sent or failed
        self.send_condition = threading.Condition()
        self.send_successful = False

        self.conn = connection.Connection()
        #: Socket connection to the server
        self.socket = create_connection(channel)

        # Send handshake with protocol version and requested bitrate
        bitrate = config.get('bitrate', 500000)
        bus_req = events.BusRequest(can.interfaces.remote.PROTOCOL_VERSION,
                                    bitrate)
        filter_conf = events.FilterConfig(can_filters)
        self.conn.send_event(bus_req)
        self.conn.send_event(filter_conf)
        self.socket.sendall(self.conn.next_data())

        event = self._next_event()
        if not isinstance(event, events.BusResponse):
            raise CanRemoteError('Handshake error')
        self.channel_info = '%s on %s' % (event.channel_info, channel)

        self.queue = queue.Queue(MAX_BUFFER_LENGTH)
        self._reader = threading.Thread(target=self._receive_from_server)
        self._reader.daemon = True
        self._reader.start()

        self.channel = channel

    def _next_event(self):
        """Block until a new event has been received.

        :return: Next event in queue
        """
        event = self.conn.next_event()
        while event is None:
            data = self.socket.recv(256)
            self.conn.receive_data(data)
            event = self.conn.next_event()
        return event

    def _receive_from_server(self):
        """Continuously receive data from server."""
        while not self.stop_event.is_set():
            event = self._next_event()
            if isinstance(event, events.CanMessage):
                self._put(event.msg)
            elif isinstance(event, events.RemoteException):
                self._put(event.exc)
            elif isinstance(event, events.TransmitSuccess):
                with self.send_condition:
                    self.send_successful = True
                    self.send_condition.notify_all()
            elif isinstance(event, events.TransmitFail):
                with self.send_condition:
                    self.send_successful = False
                    self.send_condition.notify_all()
            elif isinstance(event, events.ConnectionClosed):
                break

    def _put(self, item):
        """Add message or exception to receive queue.

        If queue is full, remove the oldest item.
        """
        while True:
            try:
                self.queue.put(item, block=False)
            except queue.Full:
                # Remove the oldest item and try again
                self.queue.get()
            else:
                break

    def recv(self, timeout=None):
        try:
            item = self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

        if isinstance(item, Exception):
            raise item

        return item

    def send(self, msg):
        with self.send_condition:
            self.conn.send_event(events.CanMessage(msg))
            self.socket.sendall(self.conn.next_data())
            self.send_successful = False
            self.send_condition.wait(2)

        if not self.send_successful:
            raise CanRemoteError('Transmission to CAN failed')

    def shutdown(self):
        """Close socket connection."""
        # Give threads a chance to finish up
        self.socket.shutdown(socket.SHUT_WR)
        self.stop_event.set()
        self._reader.join(0.5)
        self.socket.close()
        logger.debug('Network connection closed')

    def __del__(self):
        self.stop_event.set()


class CyclicSendTask(can.broadcastmanager.CyclicSendTaskABC):

    def __init__(self, channel, message, period):
        """
        :param channel: The name of the CAN channel to connect to.
        :param message: The message to be sent periodically.
        :param period: The rate in seconds at which to send the message.
        """
        super(CyclicSendTask, self).__init__(channel, message, period)
        self.message = message
        self.period = period
        self.socket = create_connection(channel)
        self.conn = connection.Connection()
        self.start()

    def __del__(self):
        self.stop()
        self.socket.close()

    def start(self):
        self._send_event(
            events.PeriodicMessageStart(self.message, self.period))

    def stop(self):
        self._send_event(
            events.PeriodicMessageStop(self.message.arbitration_id))

    def modify_data(self, message):
        assert message.arbitration_id == self.message.arbitration_id
        self._send_event(
            events.PeriodicMessageUpdate(
                self.message.arbitration_id, message.data))

    def _send_event(self, event):
        self.conn.send_event(event)
        self.socket.sendall(self.conn.next_data())


class CanRemoteError(can.CanError):
    pass

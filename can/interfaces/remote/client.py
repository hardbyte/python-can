import logging
import socket
import select
import can
from can.interfaces.remote import events
from can.interfaces.remote import connection


logger = logging.getLogger(__name__)


def create_connection(address):
    address = address.split(':')
    if len(address) >= 2:
        address = (address[0], int(address[1]))
    else:
        address = (address[0], can.interfaces.remote.DEFAULT_PORT)
    return socket.create_connection(address)


class RemoteBus(can.bus.BusABC):
    """CAN bus over a network connection bridge."""

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

        event = self._next_event(5)
        if isinstance(event, events.RemoteException):
            raise event.exc
        if not isinstance(event, events.BusResponse):
            raise CanRemoteError('Handshake error')
        self.channel_info = '%s on %s' % (event.channel_info, channel)

        self.channel = channel

    def _next_event(self, timeout=None):
        """Block until a new event has been received.

        :param float timeout: Max time in seconds to wait.
        :return: Next event received from socket (or None if timeout)
        """
        event = self.conn.next_event()
        while event is None:
            if timeout is not None and not select.select([self.socket], [], [], timeout)[0]:
                return None
            data = self.socket.recv(256)
            self.conn.receive_data(data)
            event = self.conn.next_event()
        return event

    def recv(self, timeout=None):
        """Block waiting for a message from the Bus.

        :param float timeout: Seconds to wait for a message.

        :return:
            None on timeout or a Message object.
        :rtype: can.Message
        """
        event = self._next_event(timeout)
        if isinstance(event, events.CanMessage):
            return event.msg
        elif isinstance(event, events.RemoteException):
            raise event.exc
        return None

    def send(self, msg, timeout=None):
        """Transmit a message to CAN bus.

        :param can.Message msg: A Message object.
        :raises can.interfaces.remote.CanRemoteError:
            On failed transmission to socket.
        """
        self.conn.send_event(events.CanMessage(msg))
        try:
            self.socket.sendall(self.conn.next_data())
        except OSError as e:
            raise CanRemoteError(str(e))

    def shutdown(self):
        """Close socket connection."""
        # Give threads a chance to finish up
        self.socket.shutdown(socket.SHUT_WR)
        while not isinstance(self._next_event(1), events.ConnectionClosed):
            pass
        self.socket.close()
        logger.debug('Network connection closed')


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
    """An error occurred on socket connection or on the remote end."""

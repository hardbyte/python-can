# coding: utf-8

import logging
import select
import socket
import struct
import time

import can
from can import BusABC

from utils import pack_message, unpack_message

log = logging.getLogger(__name__)


class InterprocessVirtualBus(BusABC):
    """Adds a virtual interface that allows to communicate between multiple processes.
    """

    DEFAULT_GROUP_IPv4 = '225.0.0.250'
    DEFAULT_GROUP_IPv6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'

    def __init__(self, channel=DEFAULT_GROUP_IPv6, port=43113, ttl=1,
                 receive_own_messages=False, **kwargs):
        """Construct and open a CAN bus instance.
        """
        super(InterprocessVirtualBus, self).__init__(channel, **kwargs)

        self.multicast = GeneralPurposeMulticastBus(channel, port, ttl, receive_own_messages)

    def _recv_internal(self, timeout):
        result = self.multicast.recv(timeout)
        if not result:
            return None, False

        data, _ = result
        can_message = unpack_message(data)
        return can_message, False

    def send(self, msg, timeout=None):
        """Transmit a message to the CAN bus.

        Override this method to enable the transmit path.

        :param can.Message msg: A message object.

        :type timeout: float or None
        :param timeout:
            If > 0, wait up to this many seconds for message to be ACK'ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.
            None blocks indefinitly.

        :raises can.CanError:
            if the message could not be sent
        """
        data = pack_message(msg)
        self.multicast.send(data)

    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus.
        """
        self.multicast.shutdown()

    @staticmethod
    def _detect_available_configs():
        """Detect all configurations/channels that this interface could
        currently connect with.

        This might be quite time consuming.

        May not to be implemented by every interface on every platform.

        :rtype: Iterator[dict]
        :return: an iterable of dicts, each being a configuration suitable
                 for usage in the interface's bus constructor.
        """
        return (
            {
                'interface': 'interprocess_virtual',
                'channel': InterprocessVirtualBus.DEFAULT_GROUP_IPv6
            },
            {
                'interface': 'interprocess_virtual',
                'channel': InterprocessVirtualBus.DEFAULT_GROUP_IPv4
            }
        )


class GeneralPurposeMulticastBus(object):
    """A general purpose send and receive handler for multicast over IP.
    """

    def __init__(self, group, port, ttl, receive_own_messages):
        self.group = group
        self.port = port
        self.ttl = ttl
        self.receive_own_messages = receive_own_messages  # TODO actually use this

        # Look up multicast group address in name server and find out IP version
        self._addrinfo = socket.getaddrinfo(group, None)[0]
        self.ip_version = 4 if self._addrinfo[0] == socket.AF_INET else 6

        self._socket_send = self._create_send_socket()
        self._socket_receive = self._create_receive_socket()

    def _create_send_socket(self):
        sock = socket.socket(self._addrinfo[0], socket.SOCK_DGRAM)

        # set TTL
        ttl_bin = struct.pack('@i', self.ttl)

        if self.ip_version == 4:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        else:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

        return sock

    def _create_receive_socket(self):
        sock = socket.socket(self._addrinfo[0], socket.SOCK_DGRAM)

        # Allow multiple programs to access that address + port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind it to the port
        sock.bind(('', self.port))

        # Join group
        group_bin = socket.inet_pton(self._addrinfo[0], self._addrinfo[4][0])

        if self.ip_version == 4:
            request = group_bin + struct.pack('=I', socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)
        else:
            request = group_bin + struct.pack('@I', 0)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, request)

        return sock

    def send(self, data):
        """
        Send this data to all participants.

        :param bytes data: the data to be sent
        """
        self._socket_send.sendto(data, (self._addrinfo[4][0], self.port))

    def recv(self, timeout):
        # get all sockets that are ready (can be a list with a single value
        # being self.socket or an empty list if self.socket is not ready)
        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select([self._socket_receive], [], [], timeout)
        except socket.error as exc:
            # something bad happened (e.g. the interface went down)
            raise can.CanError("Failed to receive: %s" % exc)

        if ready_receive_sockets: # not empty or True
            data, sender = self._socket_receive.recvfrom(1500)
            return data, sender

        # socket wasn't readable or timeout occurred
        return None

    def shutdown(self):
        self._socket_send.close()
        self._socket_receive.close()


if __name__ == "__main__":
    with InterprocessVirtualBus() as bus_1:
        with InterprocessVirtualBus() as bus_2:
            notifier = can.Notifier(bus_2, [can.Printer()])

            message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
            bus_1.send(message)

            time.sleep(2)

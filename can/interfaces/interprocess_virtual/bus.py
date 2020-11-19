# coding: utf-8

import logging
import select
import socket
import struct
import time

log = logging.getLogger(__name__)

import can
from can import BusABC

from .utils import pack_message, unpack_message

# TODO find alternative?
try:
    import fcntl
except ImportError:
    log.error("fcntl not available on this platform")


class InterprocessVirtualBus(BusABC):
    """A virtual interface that allows to communicate between multiple processes using UDP over Multicast IP.

    It supports IPv4 and IPv6, specified via the channel. This means that the channel is a multicast IP
    address. You can also specify the port and TTL (*time to live*).

    This bus does not support based on filtering message IDs on the kernel level.
    """

    DEFAULT_GROUP_IPv4 = '225.0.0.250'
    DEFAULT_GROUP_IPv6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'

    def __init__(self, channel=DEFAULT_GROUP_IPv6, port=43113, ttl=1,
                 receive_own_messages=False, is_fd=True, **kwargs):
        """Creates a new interprocess virtual bus.

        :param channel: An IPv4/IPv6 multicast address.
                        See `Wikipedia <https://en.wikipedia.org/wiki/IP_multicast>`__ for more details.
        :param receive_own_messages:
            If transmitted messages should also be received by this bus.
        :param fd:
            If CAN-FD frames should be supported. If set to false, an error will be raised upon sending such a
            frame and such received frames will be ignored.
        :param can_filters:
            See :meth:`can.BusABC.set_filters`.
        """
        super().__init__(channel, **kwargs)

        self.is_fd = is_fd
        self.multicast = GeneralPurposeMulticastBus(channel, port, ttl, receive_own_messages)

    def _recv_internal(self, timeout):
        result = self.multicast.recv(timeout)
        if not result:
            return None, False

        data, _, timestamp = result
        can_message = unpack_message(data, replace={'timestamp': timestamp})

        if not self.is_fd and can_message.is_fd:
            return None, False

        return can_message, False

    def send(self, message, timeout=None):
        if not self.is_fd and message.is_fd:
            raise RuntimeError("cannot send FD message over bus with CAN FD disabled")

        data = pack_message(message)
        self.multicast.send(data)

    def shutdown(self):
        self.multicast.shutdown()

    @staticmethod
    def _detect_available_configs():
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


class GeneralPurposeMulticastBus:
    """A general purpose send and receive handler for multicast over IP/UDP."""

    def __init__(self, group, port, ttl, receive_own_messages, max_buffer=4096):
        self.group = group
        self.port = port
        self.ttl = ttl
        self.receive_own_messages = receive_own_messages  # TODO actually use this
        self.max_buffer = max_buffer

        # Look up multicast group address in name server and find out IP version
        self._address_info = socket.getaddrinfo(group, None)[0]
        self.ip_version = 4 if self._address_info[0] == socket.AF_INET else 6
        self._send_destination = (self._address_info[4][0], self.port)  # TODO might be replaceable

        self._socket = self._create_socket()

    def _create_socket(self):
        sock = socket.socket(self._address_info[0], socket.SOCK_DGRAM)

        # set TTL
        ttl_bin = struct.pack('@i', self.ttl)

        if self.ip_version == 4:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        else:
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

        # Allow multiple programs to access that address + port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind it to the port
        sock.bind(('', self.port))

        # Join the multicast group
        group_as_binary = socket.inet_pton(self._address_info[0], self._address_info[4][0])
        if self.ip_version == 4:
            request = group_as_binary + struct.pack('=I', socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)
        else:
            request = group_as_binary + struct.pack('@I', 0)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, request)

        return sock

    def send(self, data, start=0, count=None):
        """Send this data to all participants. This call blocks.

        :param data: the data to be sent as byte object,
                     or if size is not given (i.e. it is not zero or None) it must be
                     a readable buffer (like a bytearray)
        """
        if not count:
            self._socket.sendto(data, self._send_destination)
        else:
            data = memoryview(data)[start:start+count]
            self._socket.sendto(data, self._send_destination)

    def recv(self, timeout):
        """
        Receive up to **max_buffer** bytes.

        :returns: None on timeout or the data alongside the sender of the data
        :rtype: Union[NoneType, Tuple[bytes, Tuple]]
        """
        # get all sockets that are ready (can be a list with a single value
        # being self.socket or an empty list if self.socket is not ready)
        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select([self._socket], [], [], timeout)
        except socket.error as exc:
            # something bad happened (e.g. the interface went down)
            raise can.CanError("Failed to receive: %s" % exc)

        if ready_receive_sockets:  # not empty
            # fetch data & source address
            data, sender = self._socket.recvfrom(self.max_buffer)

            # fetch timestamp
            # TODO maybe use https://stackoverflow.com/a/13308900/3753684
            # see:           https://stackoverflow.com/a/46330410/3753684
            binary_structure = "@LL"
            SIOCGSTAMP = 0x8906
            res = fcntl.ioctl(self._socket, SIOCGSTAMP, struct.pack(binary_structure, 0, 0))
            seconds, microseconds = struct.unpack(binary_structure, res)
            timestamp = seconds + microseconds * 1e-6

            return data, sender, timestamp

        # socket wasn't readable or timeout occurred
        return None

    def shutdown(self):
        """Close all sockets and free up any resources.

        Never throws errors and only logs them.
        """
        try:
            self._socket.close()
        except OSError as exception:
            log.error("could not close IP socket: %s", exception)


if __name__ == "__main__":
    with InterprocessVirtualBus() as bus_1, \
         InterprocessVirtualBus() as bus_2:

        notifier = can.Notifier(bus_2, [can.Printer()])

        message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
        bus_1.send(message)

        time.sleep(2)

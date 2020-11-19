import logging
import select
import socket
import struct
import time

from typing import List, Optional, Tuple, Union

log = logging.getLogger(__name__)

import can
from can import BusABC
from can.typechecking import AutoDetectedConfig
from can.typechecking import ReadableBytesLike

from .utils import pack_message, unpack_message

try:
    import fcntl
except ImportError:
    log.error("fcntl not available on this platform")


# see socket.getaddrinfo()
IPv4_ADDRESS_INFO = Tuple[str, int]  # address, port
IPv6_ADDRESS_INFO = Tuple[str, int, int, int]  # address, port, flowinfo, scope_id
IP_ADDRESS_INFO = Union[IPv4_ADDRESS_INFO, IPv6_ADDRESS_INFO]

# constants
SO_TIMESTAMPNS = 35


class MulticastIpBus(BusABC):
    """A virtual interface that allows to communicate between multiple processes using UDP over Multicast IP.

    It supports IPv4 and IPv6, specified via the channel. This means that the channel is a multicast IP
    address. You can also specify the port and TTL (*time to live*).

    Platforms: Unix (including Linux 2.6.22+), not Windows

    This bus does not support filtering based on message IDs on the kernel level.
    """

    DEFAULT_GROUP_IPv4 = "225.0.0.250"
    DEFAULT_GROUP_IPv6 = "ff15:7079:7468:6f6e:6465:6d6f:6d63:6173"

    def __init__(
        self,
        channel: str = DEFAULT_GROUP_IPv6,
        port: int = 43113,
        ttl: int = 1,
        receive_own_messages: bool = False,
        is_fd: bool = True,
        **kwargs,
    ) -> None:
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
        self.multicast = GeneralPurposeMulticastIpBus(
            channel, port, ttl, receive_own_messages
        )

    def _recv_internal(self, timeout: Optional[float]):
        result = self.multicast.recv(timeout)
        if not result:
            return None, False

        data, _, timestamp = result
        can_message = unpack_message(data, replace={"timestamp": timestamp})

        if not self.is_fd and can_message.is_fd:
            return None, False

        return can_message, False

    def send(self, message: can.Message, timeout: Optional[float] = None) -> None:
        if not self.is_fd and message.is_fd:
            raise RuntimeError("cannot send FD message over bus with CAN FD disabled")

        data = pack_message(message)
        self.multicast.send(data, timeout)

    def shutdown(self) -> None:
        self.multicast.shutdown()

    @staticmethod
    def _detect_available_configs() -> List[AutoDetectedConfig]:
        return [
            {
                "interface": "interprocess_virtual",
                "channel": MulticastIpBus.DEFAULT_GROUP_IPv6,
            },
            {
                "interface": "interprocess_virtual",
                "channel": MulticastIpBus.DEFAULT_GROUP_IPv4,
            },
        ]


class GeneralPurposeMulticastIpBus:
    """A general purpose send and receive handler for multicast over IP/UDP."""

    def __init__(
        self,
        group: str,
        port: int,
        ttl: int,
        receive_own_messages: bool,
        max_buffer: int = 4096,
    ) -> None:
        self.group = group
        self.port = port
        self.ttl = ttl
        self.receive_own_messages = receive_own_messages  # TODO actually use this
        self.max_buffer = max_buffer

        # Look up multicast group address in name server and find out IP version of the first suitable target
        # and then get the address family of it (socket.AF_INET or socket.AF_INET6)
        address_family: socket.AddressFamily = socket.getaddrinfo(group, None)[0][0]
        self.ip_version = 4 if address_family == socket.AF_INET else 6
        self._send_destination = (self.group, self.port)
        self._socket = self._create_socket(address_family)

        # used in recv()
        self.received_timestamp_struct = "@II"
        ancillary_data_size = struct.calcsize(self.received_timestamp_struct)
        self.received_ancillary_buffer_size = socket.CMSG_SPACE(ancillary_data_size)

        # used by send()
        self._last_send_timeout: Optional[float] = None

    def _create_socket(self, address_family: socket.AddressFamily) -> socket.socket:
        # create a UDP socket
        sock = socket.socket(address_family, socket.SOCK_DGRAM)

        # set TTL
        ttl_as_binary = struct.pack("@I", self.ttl)
        if self.ip_version == 4:
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_as_binary)
        else:
            sock.setsockopt(
                socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_as_binary
            )

        # Allow multiple programs to access that address + port
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # set how to receive timestamps
        sock.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPNS, 1)

        # Bind it to the port (ony any interface)
        sock.bind(("", self.port))

        # Join the multicast group
        group_as_binary = socket.inet_pton(address_family, self.group)
        if self.ip_version == 4:
            request = group_as_binary + struct.pack("=I", socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, request)
        else:
            request = group_as_binary + struct.pack("@I", 0)
            sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, request)

        return sock

    def send(
        self,
        data: ReadableBytesLike,
        timeout: Optional[float] = None,
        start: int = 0,
        count: Optional[int] = None,
    ) -> None:
        """Send this data to all participants. This call blocks.

        If `count` is set to an integer, only so many bytes beginning with `start` (inclusive) are sent.

        :param timeout: the timeout in seconds after which an Exception is raised is sending has failed
        :param data: the data to be sent
        :param start: where to start the slice to be sent
        :param count: how many bytes to send or `None` to send everything
        :raises OSError: if an error occurred while writing to the underlying socket
        :raises socket.timeout: if the timeout ran out before sending was completed (this is a subclass of
                                *OSError*)
        """
        if not count:
            data_out = data
        else:
            data_out = memoryview(data)[start : start + count]

        if timeout != self._last_send_timeout:
            self._last_send_timeout = timeout
            # this applies to all blocking calls on the socket, but sending is the only one that is blocking
            self._socket.settimeout(timeout)

        bytes_sent = self._socket.sendto(data_out, self._send_destination)
        if bytes_sent < len(data_out):
            raise socket.timeout()

    def recv(
        self, timeout: Optional[float] = None
    ) -> Optional[Tuple[bytes, IP_ADDRESS_INFO, float]]:
        """
        Receive up to **max_buffer** bytes.

        :param timeout: the timeout in seconds after which `None` is returned if not data arrived
        :returns: `None` on timeout or the data alongside the sender of the data and a timestamp in seconds
        """
        # get all sockets that are ready (can be a list with a single value
        # being self.socket or an empty list if self.socket is not ready)
        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select([self._socket], [], [], timeout)
        except socket.error as exc:
            # something bad (not a timeout) happened (e.g. the interface went down)
            raise can.CanError(f"Failed to wait for IP/UDP socket: {exc}")

        if ready_receive_sockets:  # not empty
            # fetch data & source address
            (
                raw_message_data,
                ancillary_data,
                _,  # flags
                sender_address,
            ) = self._socket.recvmsg(self.max_buffer, self.received_ancillary_buffer_size)

            # fetch timestamp; this is configured in in _create_socket()
            assert len(ancillary_data) == 1, "only requested a single extra field"
            cmsg_level, cmsg_type, cmsg_data = ancillary_data[0]
            assert (
                cmsg_level == socket.SOL_SOCKET and cmsg_type == SO_TIMESTAMPNS
            ), "received control message type that was not requested"
            # see https://man7.org/linux/man-pages/man3/timespec.3.html -> struct timespec for details
            seconds, nanoseconds = struct.unpack(self.received_timestamp_struct, cmsg_data)
            timestamp = seconds + nanoseconds * 1.0e-9

            return raw_message_data, sender_address, timestamp

        # socket wasn't readable or timeout occurred
        return None

    def shutdown(self) -> None:
        """Close all sockets and free up any resources.

        Never throws errors and only logs them.
        """
        try:
            self._socket.close()
        except OSError as exception:
            log.error("could not close IP socket: %s", exception)


def main() -> None:
    with MulticastIpBus(
        channel=MulticastIpBus.DEFAULT_GROUP_IPv6
    ) as bus_1, MulticastIpBus(channel=MulticastIpBus.DEFAULT_GROUP_IPv6) as bus_2:

        notifier = can.Notifier(bus_2, [can.Printer()])

        message = can.Message(arbitration_id=0x123, data=[1, 2, 3])
        bus_1.send(message)

        time.sleep(2)


if __name__ == "__main__":
    main()

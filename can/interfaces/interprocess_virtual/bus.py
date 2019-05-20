# coding: utf-8

import logging

import ctypes
import ctypes.util
import os
import select
import socket
import struct
import time
import errno

from can import BusABC
from abc import abstractmethod

log = logging.getLogger(__name__)


class InterprocessVirtualBus(BusABC):
    """Adds a virtual interface that allows to communicate between multiple processes.
    """

    DEFAULT_GROUP_IPv4 = '225.0.0.250'
    DEFAULT_GROUP_IPv6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'

    def __init__(self, channel=0, group=DEFAULT_GROUP_IPv6, port=43113, ttl=1, **kwargs):
        """Construct and open a CAN bus instance.
        """
        super(InterprocessVirtualBus, self).__init__(channel, **kwargs)

        self.multicast = GeneralPurposeMulticastBus

    def _recv_internal(self, timeout):
        """
        :rtype: tuple[can.Message, bool] or tuple[None, bool]
        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False

        :raises can.CanError:
            if an error occurred while reading
        """
        

    @abstractmethod
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

    def flush_tx_buffer(self):
        """Discard every message that may be queued in the output buffer(s).
        """
        pass

    def shutdown(self):
        """
        Called to carry out any interface specific cleanup required
        in shutting down a bus.
        """
        pass

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
        raise NotImplementedError()


class GeneralPurposeMulticastBus(object):
    """A general purpose send and receive handler for multicast over IP.
    """

    def __init__(self, group, port, ttl):
        self.group = group
        self.port = port
        self.ttl = ttl

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
        while True:
            self._socket_send.sendto(data, (self._addrinfo[4][0], self.port))
            time.sleep(1)

    def recv(self):
        # Loop, printing any data we receive
        while True:
            data, sender = self._socket_receive.recvfrom(1500)
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            print(str(sender) + '  ' + repr(data))



try:
    import fcntl
except ImportError:
    log.error("fcntl not available on this platform")


import can
from can import Message, BusABC

# struct module defines a binary packing format:
# https://docs.python.org/3/library/struct.html#struct-format-strings
# The 32bit can id is directly followed by the 8bit data link count
# The data field is aligned on an 8 byte boundary, hence we add padding
# which aligns the data field to an 8 byte boundary.
CAN_FRAME_HEADER_STRUCT = struct.Struct("=IBB2x")


def build_can_frame(msg):
    """ CAN frame packing/unpacking (see 'struct can_frame' in <linux/can.h>)
    /**
     * struct can_frame - basic CAN frame structure
     * @can_id:  the CAN ID of the frame and CAN_*_FLAG flags, see above.
     * @can_dlc: the data length field of the CAN frame
     * @data:    the CAN frame payload.
     */
    struct can_frame {
        canid_t can_id;  /* 32 bit CAN_ID + EFF/RTR/ERR flags */
        __u8    can_dlc; /* data length code: 0 .. 8 */
        __u8    data[8] __attribute__((aligned(8)));
    };

    /**
    * struct canfd_frame - CAN flexible data rate frame structure
    * @can_id: CAN ID of the frame and CAN_*_FLAG flags, see canid_t definition
    * @len:    frame payload length in byte (0 .. CANFD_MAX_DLEN)
    * @flags:  additional flags for CAN FD
    * @__res0: reserved / padding
    * @__res1: reserved / padding
    * @data:   CAN FD frame payload (up to CANFD_MAX_DLEN byte)
    */
    struct canfd_frame {
        canid_t can_id;  /* 32 bit CAN_ID + EFF/RTR/ERR flags */
        __u8    len;     /* frame payload length in byte */
        __u8    flags;   /* additional flags for CAN FD */
        __u8    __res0;  /* reserved / padding */
        __u8    __res1;  /* reserved / padding */
        __u8    data[CANFD_MAX_DLEN] __attribute__((aligned(8)));
    };
    """
    can_id = _add_flags_to_can_id(msg)
    flags = 0
    if msg.bitrate_switch:
        flags |= CANFD_BRS
    if msg.error_state_indicator:
        flags |= CANFD_ESI
    max_len = 64 if msg.is_fd else 8
    data = bytes(msg.data).ljust(max_len, b'\x00')
    return CAN_FRAME_HEADER_STRUCT.pack(can_id, msg.dlc, flags) + data


def build_bcm_header(opcode, flags, count, ival1_seconds, ival1_usec, ival2_seconds, ival2_usec, can_id, nframes):
    # == Must use native not standard types for packing ==
    # struct bcm_msg_head {
    #     __u32 opcode; -> I
    #     __u32 flags;  -> I
    #     __u32 count;  -> I
    #     struct timeval ival1, ival2; ->  llll ...
    #     canid_t can_id; -> I
    #     __u32 nframes; -> I
    bcm_cmd_msg_fmt = "@3I4l2I0q"

    return struct.pack(bcm_cmd_msg_fmt,
                       opcode,
                       flags,
                       count,
                       ival1_seconds,
                       ival1_usec,
                       ival2_seconds,
                       ival2_usec,
                       can_id,
                       nframes)


def build_bcm_tx_delete_header(can_id, flags):
    opcode = CAN_BCM_TX_DELETE
    return build_bcm_header(opcode, flags, 0, 0, 0, 0, 0, can_id, 1)


def build_bcm_transmit_header(can_id, count, initial_period, subsequent_period,
                              msg_flags):
    opcode = CAN_BCM_TX_SETUP

    flags = msg_flags | SETTIMER | STARTTIMER

    if initial_period > 0:
        # Note `TX_COUNTEVT` creates the message TX_EXPIRED when count expires
        flags |= TX_COUNTEVT

    def split_time(value):
        """Given seconds as a float, return whole seconds and microseconds"""
        seconds = int(value)
        microseconds = int(1e6 * (value - seconds))
        return seconds, microseconds

    ival1_seconds, ival1_usec = split_time(initial_period)
    ival2_seconds, ival2_usec = split_time(subsequent_period)
    nframes = 1

    return build_bcm_header(opcode, flags, count, ival1_seconds, ival1_usec, ival2_seconds, ival2_usec, can_id, nframes)


def build_bcm_update_header(can_id, msg_flags):
    return build_bcm_header(CAN_BCM_TX_SETUP, msg_flags, 0, 0, 0, 0, 0, can_id, 1)


def dissect_can_frame(frame):
    can_id, can_dlc, flags = CAN_FRAME_HEADER_STRUCT.unpack_from(frame)
    if len(frame) != CANFD_MTU:
        # Flags not valid in non-FD frames
        flags = 0
    return can_id, can_dlc, flags, frame[8:8+can_dlc]


def create_bcm_socket(channel):
    """create a broadcast manager socket and connect to the given interface"""
    s = socket.socket(PF_CAN, socket.SOCK_DGRAM, CAN_BCM)
    if HAS_NATIVE_SUPPORT:
        s.connect((channel,))
    else:
        addr = get_addr(s, channel)
        libc.connect(s.fileno(), addr, len(addr))
    return s


def send_bcm(bcm_socket, data):
    """
    Send raw frame to a BCM socket and handle errors.
    """
    try:
        return bcm_socket.send(data)
    except OSError as e:
        base = "Couldn't send CAN BCM frame. OS Error {}: {}\n".format(e.errno, e.strerror)

        if e.errno == errno.EINVAL:
            raise can.CanError(base + "You are probably referring to a non-existing frame.")

        elif e.errno == errno.ENETDOWN:
            raise can.CanError(base + "The CAN interface appears to be down.")

        elif e.errno == errno.EBADF:
            raise can.CanError(base + "The CAN socket appears to be closed.")

        else:
            raise e


def _add_flags_to_can_id(message):
    can_id = message.arbitration_id
    if message.is_extended_id:
        log.debug("sending an extended id type message")
        can_id |= CAN_EFF_FLAG
    if message.is_remote_frame:
        log.debug("requesting a remote frame")
        can_id |= CAN_RTR_FLAG
    if message.is_error_frame:
        log.debug("sending error frame")
        can_id |= CAN_ERR_FLAG

    return can_id


def create_socket():
    """Creates a raw CAN socket. The socket will
    be returned unbound to any interface.
    """
    sock = socket.socket(PF_CAN, socket.SOCK_RAW, CAN_RAW)

    log.info('Created a socket')

    return sock


def bind_socket(sock, channel='can0'):
    """
    Binds the given socket to the given interface.

    :param socket.socket sock:
        The socket to be bound
    :raises OSError:
        If the specified interface isn't found.
    """
    log.debug('Binding socket to channel=%s', channel)
    if HAS_NATIVE_SUPPORT:
        sock.bind((channel,))
    else:
        # For Python 2.7
        addr = get_addr(sock, channel)
        libc.bind(sock.fileno(), addr, len(addr))
    log.debug('Bound socket.')


def capture_message(sock, get_channel=False):
    """
    Captures a message from given socket.

    :param socket.socket sock:
        The socket to read a message from.
    :param bool get_channel:
        Find out which channel the message comes from.

    :return: The received message, or None on failure.
    """
    # Fetching the Arb ID, DLC and Data
    try:
        if get_channel:
            if HAS_NATIVE_SUPPORT:
                cf, addr = sock.recvfrom(CANFD_MTU)
                channel = addr[0] if isinstance(addr, tuple) else addr
            else:
                data = ctypes.create_string_buffer(CANFD_MTU)
                addr = ctypes.create_string_buffer(32)
                addrlen = ctypes.c_int(len(addr))
                received = libc.recvfrom(sock.fileno(), data, len(data), 0,
                                         addr, ctypes.byref(addrlen))
                cf = data.raw[:received]
                # Figure out the channel name
                family, ifindex = struct.unpack_from("Hi", addr.raw)
                assert family == AF_CAN
                data = struct.pack("16xi", ifindex)
                res = fcntl.ioctl(sock, SIOCGIFNAME, data)
                channel = ctypes.create_string_buffer(res).value.decode()
        else:
            cf = sock.recv(CANFD_MTU)
            channel = None
    except socket.error as exc:
        raise can.CanError("Error receiving: %s" % exc)

    can_id, can_dlc, flags, data = dissect_can_frame(cf)
    #log.debug('Received: can_id=%x, can_dlc=%x, data=%s', can_id, can_dlc, data)

    # Fetching the timestamp
    binary_structure = "@LL"
    res = fcntl.ioctl(sock, SIOCGSTAMP, struct.pack(binary_structure, 0, 0))

    seconds, microseconds = struct.unpack(binary_structure, res)
    timestamp = seconds + microseconds * 1e-6

    # EXT, RTR, ERR flags -> boolean attributes
    #   /* special address description flags for the CAN_ID */
    #   #define CAN_EFF_FLAG 0x80000000U /* EFF/SFF is set in the MSB */
    #   #define CAN_RTR_FLAG 0x40000000U /* remote transmission request */
    #   #define CAN_ERR_FLAG 0x20000000U /* error frame */
    is_extended_frame_format = bool(can_id & CAN_EFF_FLAG)
    is_remote_transmission_request = bool(can_id & CAN_RTR_FLAG)
    is_error_frame = bool(can_id & CAN_ERR_FLAG)
    is_fd = len(cf) == CANFD_MTU
    bitrate_switch = bool(flags & CANFD_BRS)
    error_state_indicator = bool(flags & CANFD_ESI)

    if is_extended_frame_format:
        #log.debug("CAN: Extended")
        # TODO does this depend on SFF or EFF?
        arbitration_id = can_id & 0x1FFFFFFF
    else:
        #log.debug("CAN: Standard")
        arbitration_id = can_id & 0x000007FF

    msg = Message(timestamp=timestamp,
                  channel=channel,
                  arbitration_id=arbitration_id,
                  is_extended_id=is_extended_frame_format,
                  is_remote_frame=is_remote_transmission_request,
                  is_error_frame=is_error_frame,
                  is_fd=is_fd,
                  bitrate_switch=bitrate_switch,
                  error_state_indicator=error_state_indicator,
                  dlc=can_dlc,
                  data=data)

    #log_rx.debug('Received: %s', msg)

    return msg


class SocketcanBus(BusABC):
    """
    Implements :meth:`can.BusABC._detect_available_configs`.
    """

    def __init__(self, channel="", receive_own_messages=False, fd=False, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0' or 'can0'.
            An empty string '' will receive messages from all channels.
            In that case any sent messages must be explicitly addressed to a
            channel using :attr:`can.Message.channel`.
        :param bool receive_own_messages:
            If transmitted messages should also be received by this bus.
        :param bool fd:
            If CAN-FD frames should be supported.
        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.
        """
        self.socket = create_socket()
        self.channel = channel
        self.channel_info = "socketcan channel '%s'" % channel
        self._bcm_sockets = {}

        # set the receive_own_messages parameter
        try:
            self.socket.setsockopt(SOL_CAN_RAW,
                                   CAN_RAW_RECV_OWN_MSGS,
                                   1 if receive_own_messages else 0)
        except socket.error as e:
            log.error("Could not receive own messages (%s)", e)

        if fd:
            # TODO handle errors
            self.socket.setsockopt(SOL_CAN_RAW,
                                   CAN_RAW_FD_FRAMES,
                                   1)

        # Enable error frames
        self.socket.setsockopt(SOL_CAN_RAW,
                               CAN_RAW_ERR_FILTER,
                               0x1FFFFFFF)

        bind_socket(self.socket, channel)
        kwargs.update({'receive_own_messages': receive_own_messages, 'fd': fd})
        super(SocketcanBus, self).__init__(channel=channel, **kwargs)

    def shutdown(self):
        """Stops all active periodic tasks and closes the socket."""
        self.stop_all_periodic_tasks()
        for channel in self._bcm_sockets:
            log.debug("Closing bcm socket for channel {}".format(channel))
            bcm_socket = self._bcm_sockets[channel]
            bcm_socket.close()
        log.debug("Closing raw can socket")
        self.socket.close()

    def _recv_internal(self, timeout):
        # get all sockets that are ready (can be a list with a single value
        # being self.socket or an empty list if self.socket is not ready)
        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select([self.socket], [], [], timeout)
        except socket.error as exc:
            # something bad happened (e.g. the interface went down)
            raise can.CanError("Failed to receive: %s" % exc)

        if ready_receive_sockets: # not empty or True
            get_channel = self.channel == ""
            msg = capture_message(self.socket, get_channel)
            if not msg.channel and self.channel:
                # Default to our own channel
                msg.channel = self.channel
            return msg, self._is_filtered
        else:
            # socket wasn't readable or timeout occurred
            return None, self._is_filtered

    def send(self, msg, timeout=None):
        """Transmit a message to the CAN bus.

        :param can.Message msg: A message object.
        :param float timeout:
            Wait up to this many seconds for the transmit queue to be ready.
            If not given, the call may fail immediately.

        :raises can.CanError:
            if the message could not be written.
        """
        log.debug("We've been asked to write a message to the bus")
        logger_tx = log.getChild("tx")
        logger_tx.debug("sending: %s", msg)

        started = time.time()
        # If no timeout is given, poll for availability
        if timeout is None:
            timeout = 0
        time_left = timeout
        data = build_can_frame(msg)

        while time_left >= 0:
            # Wait for write availability
            ready = select.select([], [self.socket], [], time_left)[1]
            if not ready:
                # Timeout
                break
            sent = self._send_once(data, msg.channel)
            if sent == len(data):
                return
            # Not all data were sent, try again with remaining data
            data = data[sent:]
            time_left = timeout - (time.time() - started)

        raise can.CanError("Transmit buffer full")

    def _send_once(self, data, channel=None):
        try:
            if self.channel == "" and channel:
                # Message must be addressed to a specific channel
                if HAS_NATIVE_SUPPORT:
                    sent = self.socket.sendto(data, (channel, ))
                else:
                    addr = get_addr(self.socket, channel)
                    sent = libc.sendto(self.socket.fileno(),
                                       data, len(data), 0,
                                       addr, len(addr))
            else:
                sent = self.socket.send(data)
        except socket.error as exc:
            raise can.CanError("Failed to transmit: %s" % exc)
        return sent

    def _send_periodic_internal(self, msg, period, duration=None):
        """Start sending a message at a given period on this bus.

        The kernel's broadcast manager will be used.

        :param can.Message msg:
            Message to transmit
        :param float period:
            Period in seconds between each message
        :param float duration:
            The duration to keep sending this message at given rate. If
            no duration is provided, the task will continue indefinitely.

        :return:
            A started task instance. This can be used to modify the data,
            pause/resume the transmission and to stop the transmission.
        :rtype: can.interfaces.socketcan.CyclicSendTask

        .. note::

            Note the duration before the message stops being sent may not
            be exactly the same as the duration specified by the user. In
            general the message will be sent at the given rate until at
            least *duration* seconds.

        """
        bcm_socket = self._get_bcm_socket(msg.channel or self.channel)
        task = CyclicSendTask(bcm_socket, msg, period, duration)
        return task

    def _get_bcm_socket(self, channel):
        if channel not in self._bcm_sockets:
            self._bcm_sockets[channel] = create_bcm_socket(self.channel)
        return self._bcm_sockets[channel]

    def _apply_filters(self, filters):
        try:
            self.socket.setsockopt(SOL_CAN_RAW,
                                   CAN_RAW_FILTER,
                                   pack_filters(filters))
        except socket.error as err:
            # fall back to "software filtering" (= not in kernel)
            self._is_filtered = False
            # TODO Is this serious enough to raise a CanError exception?
            log.error('Setting filters failed; falling back to software filtering (not in kernel): %s', err)
        else:
            self._is_filtered = True

    def fileno(self):
        return self.socket.fileno()

    @staticmethod
    def _detect_available_configs():
        return [{'interface': 'socketcan', 'channel': channel}
                for channel in find_available_interfaces()]


if __name__ == "__main__":
    # TODO move below to examples?

    # Create two sockets on vcan0 to test send and receive
    #
    # If you want to try it out you can do the following (possibly using sudo):
    #
    #     modprobe vcan
    #     ip link add dev vcan0 type vcan
    #     ifconfig vcan0 up
    #
    log.setLevel(logging.DEBUG)

    def receiver(event):
        receiver_socket = create_socket()
        bind_socket(receiver_socket, 'vcan0')
        print("Receiver is waiting for a message...")
        event.set()
        print("Receiver got: ", capture_message(receiver_socket))

    def sender(event):
        event.wait()
        sender_socket = create_socket()
        bind_socket(sender_socket, 'vcan0')
        msg = Message(arbitration_id=0x01, data=b'\x01\x02\x03')
        sender_socket.send(build_can_frame(msg))
        print("Sender sent a message.")

    import threading
    e = threading.Event()
    threading.Thread(target=receiver, args=(e,)).start()
    threading.Thread(target=sender, args=(e,)).start()

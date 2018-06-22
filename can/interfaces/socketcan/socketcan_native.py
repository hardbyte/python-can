#!/usr/bin/env python
# coding: utf-8

"""
This implementation is for versions of Python that have native
can socket and can bcm socket support.

See :meth:`can.util.choose_socketcan_implementation()`.
"""

import logging

import os
import select
import socket
import struct
import errno

log = logging.getLogger('can.socketcan.native')
log_tx = log.getChild("tx")
log_rx = log.getChild("rx")

log.debug("Loading socketcan native backend")

try:
    import fcntl
except ImportError:
    log.error("fcntl not available on this platform")

try:
    socket.CAN_RAW
except:
    log.error("CAN_* properties not found in socket module. These are required to use native socketcan")

import can
from can import Message, BusABC
from can.broadcastmanager import ModifiableCyclicTaskABC, \
    RestartableCyclicTaskABC, LimitedDurationCyclicSendTaskABC
from can.interfaces.socketcan.socketcan_constants import * # CAN_RAW, CAN_*_FLAG
from can.interfaces.socketcan.socketcan_common import \
    pack_filters, find_available_interfaces, error_code_to_str

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
    data = msg.data.ljust(max_len, b'\x00')
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
    try:
        s = socket.socket(socket.PF_CAN, socket.SOCK_DGRAM, socket.CAN_BCM)
    except AttributeError:
        raise SystemExit("To use BCM sockets you need Python3.4 or higher")
    try:
        s.connect((channel,))
    except OSError as e:
        log.error("Couldn't connect a broadcast manager socket")
        raise e
    return s


def send_bcm(bcm_socket, data):
    """
    Send raw frame to a BCM socket and handle errors.

    :param bcm_socket:
    :param data:
    :return:
    """
    try:
        return bcm_socket.send(data)
    except OSError as e:
        base = "Couldn't send CAN BCM frame. OS Error {}: {}\n".format(e.errno, os.strerror(e.errno))

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


class SocketCanBCMBase(object):
    """Mixin to add a BCM socket"""

    def __init__(self, channel, *args, **kwargs):
        self.bcm_socket = create_bcm_socket(channel)
        super(SocketCanBCMBase, self).__init__(*args, **kwargs)


class CyclicSendTask(SocketCanBCMBase, LimitedDurationCyclicSendTaskABC,
                     ModifiableCyclicTaskABC, RestartableCyclicTaskABC):
    """
    A socketcan cyclic send task supports:

        - setting of a task duration
        - modifying the data
        - stopping then subsequent restarting of the task

    """

    def __init__(self, channel, message, period, duration=None):
        """
        :param str channel: The name of the CAN channel to connect to.
        :param can.Message message: The message to be sent periodically.
        :param float period: The rate in seconds at which to send the message.
        :param float duration: Approximate duration in seconds to send the message.
        """
        super(CyclicSendTask, self).__init__(channel, message, period, duration)
        self.duration = duration
        self._tx_setup(message)
        self.message = message

    def _tx_setup(self, message):
        # Create a low level packed frame to pass to the kernel
        self.can_id_with_flags = _add_flags_to_can_id(message)
        self.flags = CAN_FD_FRAME if message.is_fd else 0
        if self.duration:
            count = int(self.duration / self.period)
            ival1 = self.period
            ival2 = 0
        else:
            count = 0
            ival1 = 0
            ival2 = self.period
        header = build_bcm_transmit_header(self.can_id_with_flags, count, ival1,
                                           ival2, self.flags)
        frame = build_can_frame(message)
        log.debug("Sending BCM command")
        send_bcm(self.bcm_socket, header + frame)

    def stop(self):
        """Send a TX_DELETE message to cancel this task.

        This will delete the entry for the transmission of the CAN-message
        with the specified can_id CAN identifier. The message length for the command
        TX_DELETE is {[bcm_msg_head]} (only the header).
        """
        log.debug("Stopping periodic task")

        stopframe = build_bcm_tx_delete_header(self.can_id_with_flags, self.flags)
        send_bcm(self.bcm_socket, stopframe)

    def modify_data(self, message):
        """Update the contents of this periodically sent message.

        Note the Message must have the same :attr:`~can.Message.arbitration_id`
        like the first message.
        """
        assert message.arbitration_id == self.can_id, "You cannot modify the can identifier"
        self.message = message
        header = build_bcm_update_header(self.can_id_with_flags, self.flags)
        frame = build_can_frame(message)
        send_bcm(self.bcm_socket, header + frame)

    def start(self):
        self._tx_setup(self.message)


class MultiRateCyclicSendTask(CyclicSendTask):
    """Exposes more of the full power of the TX_SETUP opcode.

    Transmits a message `count` times at `initial_period` then
    continues to transmit message at `subsequent_period`.
    """

    def __init__(self, channel, message, count, initial_period, subsequent_period):
        super(MultiRateCyclicSendTask, self).__init__(channel, message, subsequent_period)

        # Create a low level packed frame to pass to the kernel
        frame = build_can_frame(message)
        header = build_bcm_transmit_header(
            self.can_id_with_flags,
            count,
            initial_period,
            subsequent_period,
            self.flags)

        log.info("Sending BCM TX_SETUP command")
        send_bcm(self.bcm_socket, header + frame)


def create_socket(can_protocol=None):
    """Creates a CAN socket. The socket can be BCM or RAW. The socket will
    be returned unbound to any interface.

    :param int can_protocol:
        The protocol to use for the CAN socket, either:
         * socket.CAN_RAW
         * socket.CAN_BCM.

    :return:
        * -1 if socket creation unsuccessful
        * socketID - successful creation
    """
    if can_protocol is None or can_protocol == socket.CAN_RAW:
        can_protocol = socket.CAN_RAW
        socket_type = socket.SOCK_RAW
    elif can_protocol == socket.CAN_BCM:
        can_protocol = socket.CAN_BCM
        socket_type = socket.SOCK_DGRAM

    sock = socket.socket(socket.PF_CAN, socket_type, can_protocol)

    log.info('Created a socket')

    return sock


def bind_socket(sock, channel='can0'):
    """
    Binds the given socket to the given interface.

    :param Socket sock:
        The ID of the socket to be bound
    :raise:
        :class:`OSError` if the specified interface isn't found.
    """
    log.debug('Binding socket to channel=%s', channel)
    sock.bind((channel,))
    log.debug('Bound socket.')


def capture_message(sock):
    """
    Captures a message from given socket.

    :param socket sock:
        The socket to read a message from.

    :return: The received message, or None on failure.
    """
    # Fetching the Arb ID, DLC and Data
    try:
        cf, addr = sock.recvfrom(CANFD_MTU)
    except BlockingIOError:
        log.debug('Captured no data, socket in non-blocking mode.')
        return None
    except socket.timeout:
        log.debug('Captured no data, socket read timed out.')
        return None
    except OSError:
        # something bad happened (e.g. the interface went down)
        log.exception("Captured no data.")
        return None

    can_id, can_dlc, flags, data = dissect_can_frame(cf)
    log.debug('Received: can_id=%x, can_dlc=%x, data=%s', can_id, can_dlc, data)

    # Fetching the timestamp
    binary_structure = "@LL"
    res = fcntl.ioctl(sock, SIOCGSTAMP, struct.pack(binary_structure, 0, 0))

    seconds, microseconds = struct.unpack(binary_structure, res)
    timestamp = seconds + microseconds / 1000000

    # EXT, RTR, ERR flags -> boolean attributes
    #   /* special address description flags for the CAN_ID */
    #   #define CAN_EFF_FLAG 0x80000000U /* EFF/SFF is set in the MSB */
    #   #define CAN_RTR_FLAG 0x40000000U /* remote transmission request */
    #   #define CAN_ERR_FLAG 0x20000000U /* error frame */
    is_extended_frame_format = bool(can_id & 0x80000000)
    is_remote_transmission_request = bool(can_id & 0x40000000)
    is_error_frame = bool(can_id & 0x20000000)
    is_fd = len(cf) == CANFD_MTU
    bitrate_switch = bool(flags & CANFD_BRS)
    error_state_indicator = bool(flags & CANFD_ESI)

    if is_extended_frame_format:
        log.debug("CAN: Extended")
        # TODO does this depend on SFF or EFF?
        arbitration_id = can_id & 0x1FFFFFFF
    else:
        log.debug("CAN: Standard")
        arbitration_id = can_id & 0x000007FF

    msg = Message(timestamp=timestamp,
                  arbitration_id=arbitration_id,
                  extended_id=is_extended_frame_format,
                  is_remote_frame=is_remote_transmission_request,
                  is_error_frame=is_error_frame,
                  is_fd=is_fd,
                  bitrate_switch=bitrate_switch,
                  error_state_indicator=error_state_indicator,
                  dlc=can_dlc,
                  data=data)

    log_rx.debug('Received: %s', msg)

    return msg


class SocketcanNative_Bus(BusABC):
    """
    Implements :meth:`can.BusABC._detect_available_configs`.
    """

    def __init__(self, channel, receive_own_messages=False, fd=False, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0' or 'can0'.
        :param bool receive_own_messages:
            If transmitted messages should also be received by this bus.
        :param bool fd:
            If CAN-FD frames should be supported.
        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.
        """
        self.socket = create_socket(CAN_RAW)
        self.channel = channel
        self.channel_info = "native socketcan channel '%s'" % channel

        # set the receive_own_messages paramater
        try:
            self.socket.setsockopt(socket.SOL_CAN_RAW,
                                   socket.CAN_RAW_RECV_OWN_MSGS,
                                   struct.pack('i', receive_own_messages))
        except socket.error as e:
            log.error("Could not receive own messages (%s)", e)

        if fd:
            # TODO handle errors
            self.socket.setsockopt(socket.SOL_CAN_RAW,
                                   socket.CAN_RAW_FD_FRAMES,
                                   struct.pack('i', 1))

        bind_socket(self.socket, channel)

        kwargs.update({'receive_own_messages': receive_own_messages, 'fd': fd})
        super(SocketcanNative_Bus, self).__init__(channel=channel, **kwargs)

    def shutdown(self):
        self.socket.close()

    def _recv_internal(self, timeout):
        if timeout:
            try:
                # get all sockets that are ready (can be a list with a single value
                # being self.socket or an empty list if self.socket is not ready)
                ready_receive_sockets, _, _ = select.select([self.socket], [], [], timeout)
            except OSError:
                # something bad happened (e.g. the interface went down)
                log.exception("Error while waiting for timeout")
                ready_receive_sockets = False
        else:
            ready_receive_sockets = True

        if ready_receive_sockets: # not empty or True
            return capture_message(self.socket), self._is_filtered
        else:
            # socket wasn't readable or timeout occurred
            return None, self._is_filtered

    def send(self, msg, timeout=None):
        log.debug("We've been asked to write a message to the bus")
        logger_tx = log.getChild("tx")
        logger_tx.debug("sending: %s", msg)

        if timeout:
            # Wait for write availability
            _, ready_send_sockets, _ = select.select([], [self.socket], [], timeout)
            if not ready_send_sockets:
                raise can.CanError("Timeout while sending")

        try:
            self.socket.sendall(build_can_frame(msg))
        except OSError as exc:
            error_message = error_code_to_str(exc.errno)
            raise can.CanError("can.socketcan_native failed to transmit: {}".format(error_message))

    def send_periodic(self, msg, period, duration=None):
        return CyclicSendTask(self.channel, msg, period, duration)

    def _apply_filters(self, filters):
        try:
            self.socket.setsockopt(socket.SOL_CAN_RAW,
                                   socket.CAN_RAW_FILTER,
                                   pack_filters(filters))
        except socket.error as err:
            # fall back to "software filtering" (= not in kernel)
            self._is_filtered = False
            # TODO Is this serious enough to raise a CanError exception?
            log.error('Setting filters failed; falling back to software filtering (not in kernel): %s', err)
        else:
            self._is_filtered = True

    @staticmethod
    def _detect_available_configs():
        return [{'interface': 'socketcan_native', 'channel': channel}
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

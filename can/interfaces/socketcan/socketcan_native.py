# -*- coding: utf-8 -*-

"""
This implementation is for versions of Python that have native
can socket and can bcm socket support: >3.4
"""

import logging
import select
import threading
import socket
import struct

import errno

import os

log = logging.getLogger('can.socketcan.native')
log_tx = log.getChild("tx")
log_rx = log.getChild("rx")

log.info("Loading socketcan native backend")

try:
    import fcntl
except ImportError:
    log.warning("fcntl not available on this platform")

try:
    socket.CAN_RAW
except:
    log.debug("CAN_* properties not found in socket module. These are required to use native socketcan")

import can

from can.interfaces.socketcan.socketcan_constants import *  # CAN_RAW, CAN_*_FLAG
from can.interfaces.socketcan.socketcan_common import * # parseCanFilters
from can import Message, BusABC

from can.broadcastmanager import ModifiableCyclicTaskABC, RestartableCyclicTaskABC, LimitedDurationCyclicSendTaskABC

# struct module defines a binary packing format:
# https://docs.python.org/3/library/struct.html#struct-format-strings
# The 32bit can id is directly followed by the 8bit data link count
# The data field is aligned on an 8 byte boundary, hence we add padding
# which aligns the data field to an 8 byte boundary.
can_frame_fmt = "=IB3x8s"
can_frame_size = struct.calcsize(can_frame_fmt)


def build_can_frame(can_id, data):
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
    """
    can_dlc = len(data)
    data = data.ljust(8, b'\x00')
    return struct.pack(can_frame_fmt, can_id, can_dlc, data)


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


def build_bcm_tx_delete_header(can_id):
    opcode = CAN_BCM_TX_DELETE
    return build_bcm_header(opcode, 0, 0, 0, 0, 0, 0, can_id, 1)


def build_bcm_transmit_header(can_id, count, initial_period, subsequent_period):
    opcode = CAN_BCM_TX_SETUP

    flags = SETTIMER | STARTTIMER

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


def dissect_can_frame(frame):
    can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
    return can_id, can_dlc, data[:can_dlc]


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


def send_bcm(socket, data):
    """
    Send raw frame to a BCM socket and handle errors.

    :param socket:
    :param data:
    :return:
    """
    try:
        return socket.send(data)
    except OSError as e:
        base = "Couldn't send CAN BCM frame. OS Error {}: {}\n".format(e.errno, os.strerror(e.errno))

        if e.errno == errno.EINVAL:
            raise can.CanError(
                base + "You are probably referring to a non-existing frame.")
        elif e.errno == errno.ENETDOWN:
            raise can.CanError(
                base + "The CAN interface appears to be down."
            )
        elif e.errno == errno.EBADF:
            raise can.CanError(base + "The CAN socket appears to be closed.")
        else:
            raise

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


class CyclicSendTask(SocketCanBCMBase, LimitedDurationCyclicSendTaskABC, ModifiableCyclicTaskABC, RestartableCyclicTaskABC):
    """
    A socketcan cyclic send task supports:

        - setting of a task duration
        - modifying the data
        - stopping then subsequent restarting of the task

    """

    def __init__(self, channel, message, period):
        """

        :param channel: The name of the CAN channel to connect to.
        :param message: The message to be sent periodically.
        :param period: The rate in seconds at which to send the message.
        """
        super(CyclicSendTask, self).__init__(channel, message, period, duration=None)
        self._tx_setup(message)
        self.message = message

    def _tx_setup(self, message):
        # Create a low level packed frame to pass to the kernel
        self.can_id_with_flags = _add_flags_to_can_id(message)
        header = build_bcm_transmit_header(self.can_id_with_flags, 0, 0.0, self.period)
        frame = build_can_frame(self.can_id_with_flags, message.data)
        log.debug("Sending BCM command")
        send_bcm(self.bcm_socket, header + frame)

    def stop(self):
        """Send a TX_DELETE message to cancel this task.

        This will delete the entry for the transmission of the CAN-message
        with the specified can_id CAN identifier. The message length for the command
        TX_DELETE is {[bcm_msg_head]} (only the header).
        """
        log.debug("Stopping periodic task")

        stopframe = build_bcm_tx_delete_header(self.can_id_with_flags)
        send_bcm(self.bcm_socket, stopframe)

    def modify_data(self, message):
        """Update the contents of this periodically sent message.

        Note the Message must have the same :attr:`~can.Message.arbitration_id`.
        """
        assert message.arbitration_id == self.can_id, "You cannot modify the can identifier"
        self._tx_setup(message)

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
        frame = build_can_frame(self.can_id, message.data)
        header = build_bcm_transmit_header(
            self.can_id,
            count,
            initial_period,
            subsequent_period)

        log.info("Sending BCM TX_SETUP command")
        send_bcm(self.bcm_socket, header + frame)


def createSocket(can_protocol=None):
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


def bindSocket(sock, channel='can0'):
    """
    Binds the given socket to the given interface.

    :param Socket socketID:
        The ID of the socket to be bound
    :raise:
        :class:`OSError` if the specified interface isn't found.
    """
    log.debug('Binding socket to channel=%s', channel)
    sock.bind((channel,))
    log.debug('Bound socket.')


def captureMessage(sock):
    """
    Captures a message from given socket.

    :param socket sock:
        The socket to read a message from.

    :return: The received message, or None on failure.
    """
    # Fetching the Arb ID, DLC and Data
    try:
        cf, addr = sock.recvfrom(can_frame_size)
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

    can_id, can_dlc, data = dissect_can_frame(cf)

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
                  dlc=can_dlc,
                  data=data)

    log_rx.debug('Received: %s', msg)

    return msg


class SocketcanNative_Bus(BusABC):
    channel_info = "native socketcan channel"

    def __init__(self, channel, receive_own_messages=False, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0'.
        :param bool receive_own_messages:
            If messages transmitted should also be received back.
        :param list can_filters:
            A list of dictionaries, each containing a "can_id" and a "can_mask".
        """
        self.socket = createSocket(CAN_RAW)
        self.channel = channel

        # Add any socket options such as can frame filters
        if 'can_filters' in kwargs and len(kwargs['can_filters']) > 0:
            log.debug("Creating a filtered can bus")
            self.set_filters(kwargs['can_filters'])
        try:
            self.socket.setsockopt(socket.SOL_CAN_RAW,
                                   socket.CAN_RAW_RECV_OWN_MSGS,
                                   struct.pack('i', receive_own_messages))
        except Exception as e:
            log.error("Could not receive own messages (%s)", e)

        bindSocket(self.socket, channel)
        super(SocketcanNative_Bus, self).__init__()

    def shutdown(self):
        self.socket.close()

    def recv(self, timeout=None):
        data_ready = True
        try:
            if timeout is not None:
                data_ready = len(select.select([self.socket], [], [], timeout)[0]) > 0
        except OSError:
            # something bad happened (e.g. the interface went down)
            log.exception("Error while waiting for timeout")
            return None

        if data_ready:
            return captureMessage(self.socket)
        else:
            # socket wasn't readable or timeout occurred
            return None

    def send(self, msg, timeout=None):
        log.debug("We've been asked to write a message to the bus")
        arbitration_id = msg.arbitration_id
        if msg.id_type:
            log.debug("sending an extended id type message")
            arbitration_id |= 0x80000000
        if msg.is_remote_frame:
            log.debug("requesting a remote frame")
            arbitration_id |= 0x40000000
        if msg.is_error_frame:
            log.warning("Trying to send an error frame - this won't work")
            arbitration_id |= 0x20000000
        log_tx.debug("Sending: %s", msg)
        if timeout:
            # Wait for write availability. send will fail below on timeout
            select.select([], [self.socket], [], timeout)
        try:
            bytes_sent = self.socket.send(build_can_frame(arbitration_id, msg.data))
        except OSError as exc:
            raise can.CanError("Transmit failed (%s)" % exc)
        if bytes_sent == 0:
            raise can.CanError("Transmit buffer overflow")

    def send_periodic(self, msg, period, duration=None):
        task = CyclicSendTask(self.channel, msg, period)

        if duration is not None:
            stop_timer = threading.Timer(duration, task.stop)
            stop_timer.start()

        return task

    def set_filters(self, can_filters=None):
        filter_struct = pack_filters(can_filters)
        self.socket.setsockopt(socket.SOL_CAN_RAW,
                               socket.CAN_RAW_FILTER,
                               filter_struct
                               )


if __name__ == "__main__":
    # Create two sockets on vcan0 to test send and receive
    #
    # If you want to try it out you can do the following:
    #
    #     modprobe vcan
    #     ip link add dev vcan0 type vcan
    #     ifconfig vcan0 up
    log.setLevel(logging.DEBUG)

    def receiver(e):
        receiver_socket = createSocket()
        bindSocket(receiver_socket, 'vcan0')
        print("Receiver is waiting for a message...")
        e.set()
        print("Receiver got: ", captureMessage(receiver_socket))

    def sender(e):
        e.wait()
        sender_socket = createSocket()
        bindSocket(sender_socket, 'vcan0')
        sender_socket.send(build_can_frame(0x01, b'\x01\x02\x03'))
        print("Sender sent a message.")

    import threading
    e = threading.Event()
    threading.Thread(target=receiver, args=(e,)).start()
    threading.Thread(target=sender, args=(e,)).start()

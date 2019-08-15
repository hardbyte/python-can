# coding: utf-8

"""
The main module of the socketcan interface containing most user-facing classes and methods
along some internal methods.

At the end of the file the usage of the internal methods is shown.
"""

import logging
import ctypes
import ctypes.util
import select
import socket
import struct
import time
import errno

log = logging.getLogger(__name__)
log_tx = log.getChild("tx")
log_rx = log.getChild("rx")

try:
    import fcntl
except ImportError:
    log.error("fcntl not available on this platform")


import can
from can import Message, BusABC
from can.broadcastmanager import (
    ModifiableCyclicTaskABC,
    RestartableCyclicTaskABC,
    LimitedDurationCyclicSendTaskABC,
)
from can.interfaces.socketcan.constants import *  # CAN_RAW, CAN_*_FLAG
from can.interfaces.socketcan.utils import pack_filters, find_available_interfaces


# Setup BCM struct
def bcm_header_factory(fields, alignment=8):
    curr_stride = 0
    results = []
    pad_index = 0
    for field in fields:
        field_alignment = ctypes.alignment(field[1])
        field_size = ctypes.sizeof(field[1])

        # If the current stride index isn't a multiple of the alignment
        # requirements of this field, then we must add padding bytes until we
        # are aligned
        while curr_stride % field_alignment != 0:
            results.append(("pad_{}".format(pad_index), ctypes.c_uint8))
            pad_index += 1
            curr_stride += 1

        # Now can it fit?
        # Example: If this is 8 bytes and the type requires 4 bytes alignment
        # then we can only fit when we're starting at 0. Otherwise, we will
        # split across 2 strides.
        #
        # | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
        results.append(field)
        curr_stride += field_size

    # Add trailing padding to align to a multiple of the largest scalar member
    # in the structure
    while curr_stride % alignment != 0:
        results.append(("pad_{}".format(pad_index), ctypes.c_uint8))
        pad_index += 1
        curr_stride += 1

    return type("BcmMsgHead", (ctypes.Structure,), {"_fields_": results})


# The fields definition is taken from the C struct definitions in
# <linux/can/bcm.h>
#
#     struct bcm_timeval {
#     	long tv_sec;
#     	long tv_usec;
#     };
#
#     /**
#      * struct bcm_msg_head - head of messages to/from the broadcast manager
#      * @opcode:    opcode, see enum below.
#      * @flags:     special flags, see below.
#      * @count:     number of frames to send before changing interval.
#      * @ival1:     interval for the first @count frames.
#      * @ival2:     interval for the following frames.
#      * @can_id:    CAN ID of frames to be sent or received.
#      * @nframes:   number of frames appended to the message head.
#      * @frames:    array of CAN frames.
#      */
#     struct bcm_msg_head {
#     	__u32 opcode;
#     	__u32 flags;
#     	__u32 count;
#     	struct bcm_timeval ival1, ival2;
#     	canid_t can_id;
#     	__u32 nframes;
#     	struct can_frame frames[0];
#     };
BcmMsgHead = bcm_header_factory(
    fields=[
        ("opcode", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("count", ctypes.c_uint32),
        ("ival1_tv_sec", ctypes.c_long),
        ("ival1_tv_usec", ctypes.c_long),
        ("ival2_tv_sec", ctypes.c_long),
        ("ival2_tv_usec", ctypes.c_long),
        ("can_id", ctypes.c_uint32),
        ("nframes", ctypes.c_uint32),
    ]
)


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
    data = bytes(msg.data).ljust(max_len, b"\x00")
    return CAN_FRAME_HEADER_STRUCT.pack(can_id, msg.dlc, flags) + data


def build_bcm_header(
    opcode,
    flags,
    count,
    ival1_seconds,
    ival1_usec,
    ival2_seconds,
    ival2_usec,
    can_id,
    nframes,
):
    result = BcmMsgHead(
        opcode=opcode,
        flags=flags,
        count=count,
        ival1_tv_sec=ival1_seconds,
        ival1_tv_usec=ival1_usec,
        ival2_tv_sec=ival2_seconds,
        ival2_tv_usec=ival2_usec,
        can_id=can_id,
        nframes=nframes,
    )
    return ctypes.string_at(ctypes.addressof(result), ctypes.sizeof(result))


def build_bcm_tx_delete_header(can_id, flags):
    opcode = CAN_BCM_TX_DELETE
    return build_bcm_header(opcode, flags, 0, 0, 0, 0, 0, can_id, 1)


def build_bcm_transmit_header(
    can_id, count, initial_period, subsequent_period, msg_flags, nframes=1
):
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

    return build_bcm_header(
        opcode,
        flags,
        count,
        ival1_seconds,
        ival1_usec,
        ival2_seconds,
        ival2_usec,
        can_id,
        nframes,
    )


def build_bcm_update_header(can_id, msg_flags, nframes=1):
    return build_bcm_header(CAN_BCM_TX_SETUP, msg_flags, 0, 0, 0, 0, 0, can_id, nframes)


def dissect_can_frame(frame):
    can_id, can_dlc, flags = CAN_FRAME_HEADER_STRUCT.unpack_from(frame)
    if len(frame) != CANFD_MTU:
        # Flags not valid in non-FD frames
        flags = 0
    return can_id, can_dlc, flags, frame[8 : 8 + can_dlc]


def create_bcm_socket(channel):
    """create a broadcast manager socket and connect to the given interface"""
    s = socket.socket(PF_CAN, socket.SOCK_DGRAM, CAN_BCM)
    s.connect((channel,))
    return s


def send_bcm(bcm_socket, data):
    """
    Send raw frame to a BCM socket and handle errors.
    """
    try:
        return bcm_socket.send(data)
    except OSError as e:
        base = "Couldn't send CAN BCM frame. OS Error {}: {}\n".format(
            e.errno, e.strerror
        )

        if e.errno == errno.EINVAL:
            raise can.CanError(
                base + "You are probably referring to a non-existing frame."
            )

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


class CyclicSendTask(
    LimitedDurationCyclicSendTaskABC, ModifiableCyclicTaskABC, RestartableCyclicTaskABC
):
    """
    A SocketCAN cyclic send task supports:

        - setting of a task duration
        - modifying the data
        - stopping then subsequent restarting of the task

    """

    def __init__(self, bcm_socket, messages, period, duration=None):
        """
        :param bcm_socket: An open BCM socket on the desired CAN channel.
        :param Union[Sequence[can.Message], can.Message] messages:
            The messages to be sent periodically.
        :param float period:
            The rate in seconds at which to send the messages.
        :param float duration:
            Approximate duration in seconds to send the messages for.
        """
        # The following are assigned by LimitedDurationCyclicSendTaskABC:
        #   - self.messages
        #   - self.period
        #   - self.duration
        super().__init__(messages, period, duration)

        self.bcm_socket = bcm_socket
        self._tx_setup(self.messages)

    def _tx_setup(self, messages):
        # Create a low level packed frame to pass to the kernel
        header = bytearray()
        body = bytearray()
        self.can_id_with_flags = _add_flags_to_can_id(messages[0])
        self.flags = CAN_FD_FRAME if messages[0].is_fd else 0

        if self.duration:
            count = int(self.duration / self.period)
            ival1 = self.period
            ival2 = 0
        else:
            count = 0
            ival1 = 0
            ival2 = self.period

        # First do a TX_READ before creating a new task, and check if we get
        # EINVAL. If so, then we are referring to a CAN message with the same
        # ID
        check_header = build_bcm_header(
            opcode=CAN_BCM_TX_READ,
            flags=0,
            count=0,
            ival1_seconds=0,
            ival1_usec=0,
            ival2_seconds=0,
            ival2_usec=0,
            can_id=self.can_id_with_flags,
            nframes=0,
        )
        try:
            self.bcm_socket.send(check_header)
        except OSError as e:
            if e.errno != errno.EINVAL:
                raise e
        else:
            raise ValueError(
                "A periodic Task for Arbitration ID {} has already been created".format(
                    messages[0].arbitration_id
                )
            )

        header = build_bcm_transmit_header(
            self.can_id_with_flags,
            count,
            ival1,
            ival2,
            self.flags,
            nframes=len(messages),
        )
        for message in messages:
            body += build_can_frame(message)
        log.debug("Sending BCM command")
        send_bcm(self.bcm_socket, header + body)

    def stop(self):
        """Send a TX_DELETE message to cancel this task.

        This will delete the entry for the transmission of the CAN-message
        with the specified can_id CAN identifier. The message length for the command
        TX_DELETE is {[bcm_msg_head]} (only the header).
        """
        log.debug("Stopping periodic task")

        stopframe = build_bcm_tx_delete_header(self.can_id_with_flags, self.flags)
        send_bcm(self.bcm_socket, stopframe)

    def modify_data(self, messages):
        """Update the contents of the periodically sent messages.

        Note: The messages must all have the same
        :attr:`~can.Message.arbitration_id` like the first message.

        Note: The number of new cyclic messages to be sent must be equal to the
        original number of messages originally specified for this task.

        :param Union[Sequence[can.Message], can.Message] messages:
            The messages with the new :attr:`can.Message.data`.
        """
        messages = self._check_and_convert_messages(messages)
        self._check_modified_messages(messages)

        self.messages = messages

        header = bytearray()
        body = bytearray()
        header = build_bcm_update_header(
            can_id=self.can_id_with_flags, msg_flags=self.flags, nframes=len(messages)
        )
        for message in messages:
            body += build_can_frame(message)
        log.debug("Sending BCM command")
        send_bcm(self.bcm_socket, header + body)

    def start(self):
        self._tx_setup(self.messages)


class MultiRateCyclicSendTask(CyclicSendTask):
    """Exposes more of the full power of the TX_SETUP opcode.


    """

    def __init__(self, channel, messages, count, initial_period, subsequent_period):
        super().__init__(channel, messages, subsequent_period)

        # Create a low level packed frame to pass to the kernel
        header = build_bcm_transmit_header(
            self.can_id_with_flags,
            count,
            initial_period,
            subsequent_period,
            self.flags,
            nframes=len(messages),
        )

        body = bytearray()
        for message in messages:
            body += build_can_frame(message)

        log.info("Sending BCM TX_SETUP command")
        send_bcm(self.bcm_socket, header + body)


def create_socket():
    """Creates a raw CAN socket. The socket will
    be returned unbound to any interface.
    """
    sock = socket.socket(PF_CAN, socket.SOCK_RAW, CAN_RAW)

    log.info("Created a socket")

    return sock


def bind_socket(sock, channel="can0"):
    """
    Binds the given socket to the given interface.

    :param socket.socket sock:
        The socket to be bound
    :raises OSError:
        If the specified interface isn't found.
    """
    log.debug("Binding socket to channel=%s", channel)
    sock.bind((channel,))
    log.debug("Bound socket.")


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
            cf, addr = sock.recvfrom(CANFD_MTU)
            channel = addr[0] if isinstance(addr, tuple) else addr
        else:
            cf = sock.recv(CANFD_MTU)
            channel = None
    except socket.error as exc:
        raise can.CanError("Error receiving: %s" % exc)

    can_id, can_dlc, flags, data = dissect_can_frame(cf)
    # log.debug('Received: can_id=%x, can_dlc=%x, data=%s', can_id, can_dlc, data)

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
        # log.debug("CAN: Extended")
        # TODO does this depend on SFF or EFF?
        arbitration_id = can_id & 0x1FFFFFFF
    else:
        # log.debug("CAN: Standard")
        arbitration_id = can_id & 0x000007FF

    msg = Message(
        timestamp=timestamp,
        channel=channel,
        arbitration_id=arbitration_id,
        is_extended_id=is_extended_frame_format,
        is_remote_frame=is_remote_transmission_request,
        is_error_frame=is_error_frame,
        is_fd=is_fd,
        bitrate_switch=bitrate_switch,
        error_state_indicator=error_state_indicator,
        dlc=can_dlc,
        data=data,
    )

    # log_rx.debug('Received: %s', msg)

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
        self._is_filtered = False

        # set the receive_own_messages parameter
        try:
            self.socket.setsockopt(
                SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS, 1 if receive_own_messages else 0
            )
        except socket.error as e:
            log.error("Could not receive own messages (%s)", e)

        if fd:
            # TODO handle errors
            self.socket.setsockopt(SOL_CAN_RAW, CAN_RAW_FD_FRAMES, 1)

        # Enable error frames
        self.socket.setsockopt(SOL_CAN_RAW, CAN_RAW_ERR_FILTER, 0x1FFFFFFF)

        bind_socket(self.socket, channel)
        kwargs.update({"receive_own_messages": receive_own_messages, "fd": fd})
        super().__init__(channel=channel, **kwargs)

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

        if ready_receive_sockets:  # not empty or True
            get_channel = self.channel == ""
            msg = capture_message(self.socket, get_channel)
            if not msg.channel and self.channel:
                # Default to our own channel
                msg.channel = self.channel
            return msg, self._is_filtered
        else:
            # socket wasn't readable or timeout occurred
            return None, self._is_filtered

    def _send_internal(self, msg, timeout=None):
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
                sent = self.socket.sendto(data, (channel,))
            else:
                sent = self.socket.send(data)
        except socket.error as exc:
            raise can.CanError("Failed to transmit: %s" % exc)
        return sent

    def _send_periodic_internal(self, msgs, period, duration=None):
        """Start sending messages at a given period on this bus.

        The kernel's Broadcast Manager SocketCAN API will be used.

        :param Union[Sequence[can.Message], can.Message] messages:
            The messages to be sent periodically
        :param float period:
            The rate in seconds at which to send the messages.
        :param float duration:
            Approximate duration in seconds to continue sending messages. If
            no duration is provided, the task will continue indefinitely.

        :return:
            A started task instance. This can be used to modify the data,
            pause/resume the transmission and to stop the transmission.
        :rtype: can.interfaces.socketcan.CyclicSendTask

        .. note::

            Note the duration before the messages stop being sent may not
            be exactly the same as the duration specified by the user. In
            general the message will be sent at the given rate until at
            least *duration* seconds.

        """
        msgs = LimitedDurationCyclicSendTaskABC._check_and_convert_messages(msgs)

        bcm_socket = self._get_bcm_socket(msgs[0].channel or self.channel)
        # TODO: The SocketCAN BCM interface treats all cyclic tasks sharing an
        # Arbitration ID as the same Cyclic group. We should probably warn the
        # user instead of overwriting the old group?
        task = CyclicSendTask(bcm_socket, msgs, period, duration)
        return task

    def _get_bcm_socket(self, channel):
        if channel not in self._bcm_sockets:
            self._bcm_sockets[channel] = create_bcm_socket(self.channel)
        return self._bcm_sockets[channel]

    def _apply_filters(self, filters):
        try:
            self.socket.setsockopt(SOL_CAN_RAW, CAN_RAW_FILTER, pack_filters(filters))
        except socket.error as err:
            # fall back to "software filtering" (= not in kernel)
            self._is_filtered = False
            # TODO Is this serious enough to raise a CanError exception?
            log.error(
                "Setting filters failed; falling back to software filtering (not in kernel): %s",
                err,
            )
        else:
            self._is_filtered = True

    def fileno(self):
        return self.socket.fileno()

    @staticmethod
    def _detect_available_configs():
        return [
            {"interface": "socketcan", "channel": channel}
            for channel in find_available_interfaces()
        ]


if __name__ == "__main__":
    # This example demonstrates how to use the internal methods of this module.
    # It creates two sockets on vcan0 to test sending and receiving.
    #
    # If you want to try it out you can do the following (possibly using sudo):
    #
    #     modprobe vcan
    #     ip link add dev vcan0 type vcan
    #     ip link set vcan0 up
    #
    log.setLevel(logging.DEBUG)

    def receiver(event):
        receiver_socket = create_socket()
        bind_socket(receiver_socket, "vcan0")
        print("Receiver is waiting for a message...")
        event.set()
        print(f"Receiver got: {capture_message(receiver_socket)}")

    def sender(event):
        event.wait()
        sender_socket = create_socket()
        bind_socket(sender_socket, "vcan0")
        msg = Message(arbitration_id=0x01, data=b"\x01\x02\x03")
        sender_socket.send(build_can_frame(msg))
        print("Sender sent a message.")

    import threading

    e = threading.Event()
    threading.Thread(target=receiver, args=(e,)).start()
    threading.Thread(target=sender, args=(e,)).start()

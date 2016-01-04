# -*- coding: utf-8 -*-

"""
This implementation is for versions of Python that have native
can socket and can bcm socket support: >3.4
"""

import socket
import fcntl
import struct
import logging
from collections import namedtuple
import select

log = logging.getLogger('can.socketcan.native')
#log.setLevel(logging.DEBUG)
log.debug("Loading native socket can implementation")

try:
    socket.CAN_RAW
except:
    log.error("Note Python 3.3 or later is required to use native socketcan")
    raise ImportError()


from can import Message
from can.interfaces.socketcan_constants import *  # CAN_RAW
from ..bus import BusABC

from ..broadcastmanager import CyclicSendTaskABC

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
    bcm_cmd_msg_fmt = "@IIIllllII"

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
    return (can_id, can_dlc, data[:can_dlc])


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


class CyclicSendTask(CyclicSendTaskABC):

    def __init__(self, channel, message, period):
        """

        :param channel: The name of the CAN channel to connect to.
        :param message: The message to be sent periodically.
        :param period: The rate in seconds at which to send the message.
        """
        super(CyclicSendTask,self).__init__(channel, message, period)
        self.bcm_socket = create_bcm_socket(channel)
        self._tx_setup(message)

    def _tx_setup(self, message):
        # Create a low level packed frame to pass to the kernel
        header = build_bcm_transmit_header(self.can_id, 0, 0.0, self.period)
        frame = build_can_frame(self.can_id, message.data)
        log.info("Sending BCM command")
        self.bcm_socket.send(header + frame)

    def stop(self):
        """Send a TX_DELETE message to cancel this task.

        This will delete the entry for the transmission of the CAN-message
        with the specified can_id CAN identifier. The message length for the command
        TX_DELETE is {[bcm_msg_head]} (only the header).
        """
        try:
            self.bcm_socket.send(build_bcm_tx_delete_header(self.can_id))
        except:
            pass

    def modify_data(self, message):
        """Update the contents of this periodically sent message.
        """
        assert message.arbitration_id == self.can_id, "You cannot modify the can identifier"
        self._tx_setup(message)


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

_CanPacket = namedtuple('_CanPacket',
                        ['timestamp',
                         'arbitration_id',
                         'is_error_frame',
                         'is_extended_frame_format',
                         'is_remote_transmission_request',
                         'dlc',
                         'data'])


def capturePacket(sock):
    """
    Captures a packet of data from the given socket.

    :param socket sock:
        The socket to read a packet from.

    :return: A namedtuple with the following fields:
         * timestamp
         * arbitration_id
         * is_extended_frame_format
         * is_remote_transmission_request
         * is_error_frame
         * dlc
         * data
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

    can_id, can_dlc, data = dissect_can_frame(cf)
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
    CAN_EFF_FLAG = bool(can_id & 0x80000000)
    CAN_RTR_FLAG = bool(can_id & 0x40000000)
    CAN_ERR_FLAG = bool(can_id & 0x20000000)

    if CAN_EFF_FLAG:
        log.debug("CAN: Extended")
        # TODO does this depend on SFF or EFF?
        arbitration_id = can_id & 0x1FFFFFFF
    else:
        log.debug("CAN: Standard")
        arbitration_id = can_id & 0x000007FF

    return _CanPacket(timestamp, arbitration_id, CAN_ERR_FLAG, CAN_EFF_FLAG, CAN_RTR_FLAG, can_dlc, data)


class SocketscanNative_Bus(BusABC):
    channel_info = "native socketcan channel"

    def __init__(self, channel, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0'.

        :param list can_filters:
            A list of dictionaries, each containing a "can_id" and a "can_mask".
        """
        self.socket = createSocket(CAN_RAW)

        # Add any socket options such as can frame filters
        if 'can_filters' in kwargs and len(kwargs['can_filters']) > 0:
            log.debug("Creating a filtered can bus")
            can_filter_fmt = "={}I".format(2 * len(kwargs['can_filters']))
            filter_data = []
            for can_filter in kwargs['can_filters']:
                filter_data.append(can_filter['can_id'])
                filter_data.append(can_filter['can_mask'])

            self.socket.setsockopt(socket.SOL_CAN_RAW,
                                   socket.CAN_RAW_FILTER,
                                   struct.pack(can_filter_fmt, *filter_data),
                                   )
        bindSocket(self.socket, channel)
        super(SocketscanNative_Bus, self).__init__()

    def __del__(self):
        self.socket.close()

    def recv(self, timeout=None):

        if timeout is None or len(select.select([self.socket],
                                                [], [], timeout)[0]) > 0:
            packet = capturePacket(self.socket)

            # The capturePacket function can return None if
            # self.socket.settimeout has been called.
            if packet is None:
                return None
        else:
            # socket wasn't readable or timeout occurred
            return None

        rx_msg = Message(timestamp=packet.timestamp,
                         arbitration_id=packet.arbitration_id,
                         extended_id=packet.is_extended_frame_format,
                         is_remote_frame=packet.is_remote_transmission_request,
                         is_error_frame=packet.is_error_frame,
                         dlc=packet.dlc,
                         data=packet.data
                         )

        return rx_msg

    def send(self, message):
        log.debug("We've been asked to write a message to the bus")
        arbitration_id = message.arbitration_id
        if message.id_type:
            log.debug("sending an extended id type message")
            arbitration_id |= 0x80000000
        if message.is_remote_frame:
            log.debug("requesting a remote frame")
            arbitration_id |= 0x40000000
        if message.is_error_frame:
            log.warning("Trying to send an error frame - this won't work")
            arbitration_id |= 0x20000000
        l = log.getChild("tx")
        l.debug("sending: %s", message)
        try:
            self.socket.send(build_can_frame(arbitration_id, message.data))
        except OSError:
            l.warning("Failed to send: %s", message)


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
        print("Receiver got: ", capturePacket(receiver_socket))

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

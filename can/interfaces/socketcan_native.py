# -*- coding: utf-8 -*-

"""
This implementation is for versions of Python that have native
can socket support: >3.3
"""

import socket
import fcntl
import struct
import logging
from collections import namedtuple

log = logging.getLogger('can.socketcan_native')
#log.setLevel(logging.DEBUG)
log.debug("Loading native socket can implementation")

try:
    socket.CAN_RAW
except:
    log.error("Python 3.3 or later required to use native socketcan")

from can import Message
from can.interfaces.socketcan_constants import *   #CAN_RAW
from ..bus import BusABC

can_frame_fmt = "=IB3x8s"
can_frame_size = struct.calcsize(can_frame_fmt)

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

def build_can_frame(can_id, data):
    can_dlc = len(data)
    data = data.ljust(8, b'\x00')
    return struct.pack(can_frame_fmt, can_id, can_dlc, data)


def dissect_can_frame(frame):
    can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
    return (can_id, can_dlc, data[:can_dlc])


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
    log.debug('Binding socket to channel={}'.format(channel))
    sock.bind((channel,))

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
    cf, addr = sock.recvfrom(can_frame_size)
    
    can_id, can_dlc, data = dissect_can_frame(cf)
    log.debug('Received: can_id=%x, can_dlc=%x, data=%s' % (can_id, can_dlc, data))
    
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


class Bus(BusABC):
    channel_info = "native socketcan channel"
    
    def __init__(self, channel, *args, **kwargs):
        self.socket = createSocket(CAN_RAW)
        bindSocket(self.socket, channel)
        super(Bus, self).__init__(*args, **kwargs)

    def _get_message(self, timeout=None):

        # TODO socketcan error checking...?
        packet = capturePacket(self.socket)

        rx_msg = Message(timestamp=packet.timestamp,
                         arbitration_id=packet.arbitration_id,
                         extended_id=packet.is_extended_frame_format,
                         is_remote_frame=packet.is_remote_transmission_request,
                         is_error_frame=packet.is_error_frame,
                         dlc=packet.dlc,
                         data=packet.data
                         )

        return rx_msg

    def _put_message(self, message):
        log.debug("We've been asked to write a message to the bus")
        arbitration_id = message.arbitration_id
        if message.id_type:
            log.debug("sending an extended id type message")
            arbitration_id |= 0x80000000
        if message.is_remote_frame:
            log.debug("requesting a remote frame")
            arbitration_id |= 0x40000000
        if message.is_error_frame:
            log.debug("sending error frame")
            arbitration_id |= 0x20000000

        self.socket.send(build_can_frame(arbitration_id, message.data))


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
    


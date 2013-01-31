# -*- coding: utf-8 -*-

"""
This implementation is for versions of Python that have native
can socket support: >3.3
"""

import socket
import fcntl
import struct
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('can.socketcan_native')

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

def build_can_frame(can_id, data):
    can_dlc = len(data)
    data = data.ljust(8, b'\x00')
    return struct.pack(can_frame_fmt, can_id, can_dlc, data)

def dissect_can_frame(frame):
    can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
    return (can_id, can_dlc, data[:can_dlc])


def createSocket(can_protocol=None):
    '''Creates a CAN socket. The socket can be BCM or RAW. The socket will
    be returned unbound to any interface.

    :param int can_protocol:
        The protocol to use for the CAN socket, either:
         * socket.CAN_RAW
         * socket.CAN_BCM.

    :return:
        * -1 if socket creation unsuccessful
        * socketID - successful creation
    '''
    if can_protocol is None:
        can_protocol = socket.CAN_RAW
    if can_protocol == socket.CAN_RAW:
        sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    elif can_protocol == socket.CAN_BCM:
        sock = socket.socket(socket.PF_CAN, socket.SOCK_DGRAM, socket.CAN_BCM)
    log.info('Created a socket')

    return sock


def bindSocket(sock, channel='can0'):
    '''
    Binds the given socket to the given interface.

    :param Socket socketID:
        The ID of the socket to be bound
    :raise:
        :class:`OSError` if the specified interface isn't found.
    '''
    log.debug('Binding socket to channel={}'.format(channel))
    sock.bind((channel,))


def capturePacket(sock):
    '''
    Captures a packet of data from the given socket.
    
    :param socket sock:
        The socket to read a packet from.
    
    :return: A dictionary with the following keys:
        'CAN ID',
        'DLC'
        'Data' 
        'Timestamp'
    '''
    
    # Fetching the Arb ID, DLC and Data
    cf, addr = sock.recvfrom(can_frame_size)
    
    can_id, can_dlc, data = dissect_can_frame(cf)
    log.debug('Received: can_id=%x, can_dlc=%x, data=%s' % (can_id, can_dlc, data))
    
    # Fetching the timestamp
    binary_structure = "@LL"
    res = fcntl.ioctl(sock, SIOCGSTAMP, struct.pack(binary_structure, 0, 0))

    seconds, microseconds = struct.unpack(binary_structure, res)
    timestamp = seconds + microseconds/1000000

    return {
        'CAN ID': can_id,
        'DLC': can_dlc,
        'Data': data,
        'Timestamp': timestamp,
    }

class Bus(BusABC):
    channel_info = "native socketcan channel"
    
    def __init__(self, channel, *args, **kwargs):

        self.socketID = createSocket(CAN_RAW)
        bindSocket(self.socketID, channel)

        super(Bus, self).__init__(*args, **kwargs)


    def _get_message(self):
        
        rx_msg = Message()

        # TODO socketcan error checking...?
        packet = capturePacket(self.socketID)

        arbitration_id = packet['CAN ID'] & MSK_ARBID

        # TODO flags could just be boolean attributes?
        # Flags: EXT, RTR, ERR
        flags = (packet['CAN ID'] & MSK_FLAGS) >> 29

        # To keep flags consistent with pycanlib, their positions need to be switched around
        flags = (flags | PYCAN_ERRFLG) & ~(SKT_ERRFLG) if flags & SKT_ERRFLG else flags 
        flags = (flags | PYCAN_RTRFLG) & ~(SKT_RTRFLG) if flags & SKT_RTRFLG else flags
        flags = (flags | PYCAN_STDFLG) & ~(EXTFLG) if not(flags & EXTFLG) else flags

        if flags & EXTFLG:
            rx_msg.id_type = ID_TYPE_EXTENDED
            log.debug("CAN: Extended")
        else:
            rx_msg.id_type = ID_TYPE_STANDARD
            log.debug("CAN: Standard")

        rx_msg.arbitration_id = arbitration_id
        rx_msg.dlc = packet['DLC']
        rx_msg.flags = flags
        rx_msg.data = packet['Data']
        rx_msg.timestamp = packet['Timestamp']
        
        return rx_msg


if __name__ == "__main__":
    '''Create two sockets on vcan0 to test send and receive
    
    If you want to try it out you can do the following:
        modprobe vcan
        ip link add dev vcan0 type vcan
        ifconfig vcan0 up
    '''

    def receiver():
        receiver_socket = createSocket()
        bindSocket(receiver_socket, 'vcan0')
        print("Receiver is waiting for a message...")
        print("Receiver got: ", capturePacket(receiver_socket))

    def sender():
        sender_socket = createSocket()
        bindSocket(sender_socket, 'vcan0')
        sender_socket.send(build_can_frame(0x01, b'\x01\x02\x03'))
        print("Sender sent a message.")

    import threading
    threading.Thread(target=receiver).start()
    
    threading.Thread(target=sender).start()
    


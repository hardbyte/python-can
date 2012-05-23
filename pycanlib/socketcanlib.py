"""
This implementation is for versions of Python that do not have native
can socket support. It works by wrapping libc calls for Python.
"""

import socket
import struct
import sys
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('pycan')

log.debug("Loading native socket can implementation")


can_frame_fmt = "=IB3x8s"
can_frame_size = struct.calcsize(can_frame_fmt)

def build_can_frame(can_id, data):
    can_dlc = len(data)
    data = data.ljust(8, b'\x00')
    return struct.pack(can_frame_fmt, can_id, can_dlc, data)

def dissect_can_frame(frame):
    can_id, can_dlc, data = struct.unpack(can_frame_fmt, frame)
    return (can_id, can_dlc, data[:can_dlc])


def createSocket(canProtocol=socket.CAN_RAW):
    '''Creates a CAN socket. The socket can be BCM or RAW. The socket will
    be returned unbound to any inteface.

    :param int canProtocol:
        The protocol to use for the CAN socket, either:
         * socket.CAN_RAW
         * socket.CAN_BCM.

    :return:
        -1 - socket creation unsuccessful
        socketID - successful creation
    '''
    if canProtocol == socket.CAN_RAW:
        sock = socket.socket(socket.PF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
    elif canProtocol == socket.CAN_BCM:
        sock = socket.socket(socket.PF_CAN, socket.SOCK_DGRAM, socket.CAN_BCM)
    log.info('Created a socket')
    return sock


def bindSocket(sock, channel='can0'):
    '''
    Binds the given socket to the given interface.

    :param socket.Socket socketID:
        The ID of the socket to be bound

    :return:

    '''
    log.debug('Binding socket to channel={}'.format(channel))
    sock.bind((channel,))


def capturePacket(sock):
    '''
    Captures a packet of data from the given socket.
    :param sock:
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
    print('Received: can_id=%x, can_dlc=%x, data=%s' % (can_id, can_dlc, data))
    
    # Fetching the timestamp - TODO
    #error = libc.ioctl(socketID, SIOCGSTAMP, ctypes.byref(time));
    
    # The first 3 elements in the data array are discarded (as they are
    # empty) and the rest (actual data) saved into a list. TODO why????
    #data = []
    #for i in range(3, can_dlc + 3):
    #    data.append(data[i])
    return {
        'CAN ID': can_id,
        'DLC': can_dlc,
        'Data': data,
        'Timestamp': 0.0,
    }

if __name__ == "__main__":
    '''Create two sockets on vcan0 to test send and receive
    If you want to try it out (just for fun :-), you can do the following:
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
    

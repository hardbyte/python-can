from __future__ import print_function
import sys
import ctypes
import logging
import select

from ctypes.util import find_library

from can.interfaces.socketcan_constants import *   #CAN_RAW
from ..bus import BusABC
from ..message import Message

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.socketcan_ctypes')

class Bus(BusABC):
    """
    An implementation of the :class:`can.bus.BusABC` for SocketCAN using :mod:`ctypes`.
    """
    channel_info = "ctypes socketcan channel"

    def __init__(self,
                 channel,
                 *args, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0'.
        """    

        self.socket = createSocket()
        
        log.debug("Result of createSocket was {}".format(self.socket))
        error = bindSocket(self.socket, channel)
        super(Bus, self).__init__(*args, **kwargs)

        
    def recv(self, timeout=None):
        rx_msg = Message()

        log.debug("Trying to read a msg")

        if timeout is None or len( select.select([socketID], [], [], timeout=timeout)[0]) > 0:
            packet = capturePacket(self.socket)
        else:
            # socket wasn't readable
            return None

        log.debug("I've got a message")

        arbitration_id = packet['CAN ID'] & MSK_ARBID

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
    

    def send(self, msg):
        sendPacket(self.socket, msg)


log.debug("Loading libc with ctypes...")
#libc = ctypes.cdll.LoadLibrary("libc.so.6")
libc = ctypes.cdll.LoadLibrary(find_library("c"))

start_sec = 0
start_usec = 0
SEC_USEC = 1000000

# See /usr/include/i386-linux-gnu/bits/socket.h for original struct
class SOCKADDR(ctypes.Structure):
    _fields_ = [("sa_family", ctypes.c_uint16),
                ("sa_data", (ctypes.c_char)*14) ]


# This struct is only used within the SOCKADDR_CAN struct
class TP(ctypes.Structure):
    _fields_ = [("rx_id", ctypes.c_uint32),
                ("tx_id", ctypes.c_uint32)]


# This struct is only used within the SOCKADDR_CAN struct
class ADDR_INFO(ctypes.Union):
    # This union is to future proof for future can address information
    _fields_ = [("tp", TP)]


# See /usr/include/linux/can.h for original struct
class SOCKADDR_CAN(ctypes.Structure):
    _fields_ = [("can_family", ctypes.c_uint16),
                ("can_ifindex", ctypes.c_int),
                ("can_addr", ADDR_INFO)]


# The two fields in this struct were originally unions.
# See /usr/include/net/if.h for original struct
class IFREQ(ctypes.Structure):
    _fields_ = [("ifr_name", ctypes.c_char*16),
                ("ifr_ifindex", ctypes.c_int)]


# Aligns the data field to an 8 byte boundary
# Removed because pypy's ctypes can't seem to handle the anonymous inner field
#class _AnonDataField(ctypes.Structure):
#    _pack_ = 8
#    _fields_ = [("data", (ctypes.c_uint8)*8)]

# See /usr/include/linux/can.h for original struct
# The 32bit can id is directly followed by the 8bit data link count
# The data field is aligned on an 8 byte boundary, hence the padding.
class CAN_FRAME(ctypes.Structure):
    #_anonymous_ = ("u",)
    _fields_ = [("can_id", ctypes.c_uint32),
                ("can_dlc", ctypes.c_uint8),
                #("u", _AnonDataField)
                ("padding", ctypes.c_ubyte*3),
                ("data", ctypes.c_uint8*8)
                ]


# See usr/include/linux/time.h for original struct
class TIME_VALUE(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_ulong),
                ("tv_usec", ctypes.c_ulong)]


def createSocket(protocol=CAN_RAW):
    """
    This function creates a RAW CAN socket.

    The socket returned needs to be bound to an interface by calling
    :func:`bindSocket`.

    Returns:
        +-----------+----------------------------+
        | 0         |protocol invalid            |
        +-----------+----------------------------+
        | -1        |socket creation unsuccessful|
        +-----------+----------------------------+
        | socketID  |  successful creation       |
        +-----------+----------------------------+
    """
    if protocol == CAN_RAW:
        socketID = libc.socket(PF_CAN, SOCK_RAW, CAN_RAW)
    elif protocol == CAN_BCM:
        socketID = libc.socket(PF_CAN, SOCK_DGRAM, CAN_BCM)
    else:
        socketID = 0
        
    return socketID


def bindSocket(socketID, channel_name):
    """
    Binds the given socket to the given interface.

    :param int socketID:
        The ID of the socket to be bound

    :param str channel_name:
        The interface name to find and bind.

    :return The error code from the bind call.
        +-----------+----------------------------+
        | 0         |protocol invalid            |
        +-----------+----------------------------+
        | -1        |socket creation unsuccessful|
        +-----------+----------------------------+
    """
    log.debug('Binding socket with id {} to channel {}'.format(socketID, channel_name))
    socketID = ctypes.c_int(socketID)
    
    ifr = IFREQ()
    ifr.ifr_name = channel_name.encode('ascii')
    log.debug('calling ioctl SIOCGIFINDEX')
    # ifr.ifr_ifindex gets filled with that device's index
    libc.ioctl(socketID, SIOCGIFINDEX, ctypes.byref(ifr))
    log.info('ifr.ifr_ifindex: {}'.format(ifr.ifr_ifindex))
    
    # select the CAN interface and bind the socket to it
    addr = SOCKADDR_CAN(AF_CAN, ifr.ifr_ifindex)

    error = libc.bind(socketID, ctypes.byref(addr), ctypes.sizeof(addr))

    if error < 0:
        log.error("Couldn't bind socket")
    log.debug('bind returned: {}'.format(error))

    return error

def sendPacket(socket, message):
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
    log.debug("Data: {}".format(message.data))
    log.debug("type: {}".format(type(message.data)))
    
    # TODO could see what is the fastest way to do this
    #mtype = (ctypes.c_uint8 * 8 )
    #ctypes_data = mtype.from_buffer_copy( message.data + bytearray([0] * (8 - len(message.data))))
    # Also need to understand the extended frame format
    #assert len(message.data) <= 8, type(message.data)
    frame = CAN_FRAME()
    frame.can_id = arbitration_id
    frame.can_dlc = len(message.data)
    
    for i in range(len(message.data)):
        frame.data[i] = message.data[i]
    #frame.data = ctypes_data
    
    log.debug("sizeof frame: {}".format(ctypes.sizeof(frame)))
    bytes_sent = libc.write(socket,
                            ctypes.byref(frame),
                            ctypes.sizeof(frame))
    if bytes_sent == -1:
        logging.error("Error sending frame :-/")
        
    #print("Bytes sent: ", bytes_sent)
    return bytes_sent


def capturePacket(socketID):
    """
    Captures a packet of data from the given socket.

    :param int socketID:
        The socket to read from

    :return:
        A dictionary with the following keys:
        +-----------+----------------------------+
        | 'CAN ID'  |  int                       |
        +-----------+----------------------------+
        | 'DLC'     |  int                       |
        +-----------+----------------------------+
        | 'Data'    |  list                      |
        +-----------+----------------------------+
        |'Timestamp'|   float                    |
        +-----------+----------------------------+

    """
    packet = {}
    
    frame = CAN_FRAME()
    time = TIME_VALUE()
    
    # Fetching the Arb ID, DLC and Data
    bytes_read = libc.read(socketID, ctypes.byref(frame), sys.getsizeof(frame))

    # Fetching the timestamp
    error = libc.ioctl(socketID, SIOCGSTAMP, ctypes.byref(time))
    
    packet['CAN ID'] = frame.can_id
    packet['DLC'] = frame.can_dlc
    packet["Data"] = [frame.data[i] for i in range(frame.can_dlc)]

    timestamp = time.tv_sec + (time.tv_usec / 1000000)
    
    packet['Timestamp'] = timestamp

    return packet


if __name__ == "__main__":
    socket_id = createSocket(CAN_RAW)
    print("Created socket (id = {})".format(socket_id))
    print(bindSocket(socket_id))


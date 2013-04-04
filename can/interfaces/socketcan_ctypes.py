
import sys
import ctypes
import logging


from can.interfaces.socketcan_constants import *   #CAN_RAW
from ..bus import BusABC
from ..message import Message

# Set up logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('can.socketcan_ctypes')


class Bus(BusABC):
    """
    An implementation of the :class:`can.bus.BusABC` for SocketCAN using :mod:`ctypes`.
    """
    
    def __init__(self,
                 channel,
                 *args, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0'.
        """    

        self.socketID = createSocket()
        
        log.debug("Result of createSocket was {}".format(self.socketID))
        
        bindSocket(self.socketID, channel)
        
        super(Bus, self).__init__(*args, **kwargs)
        

        
    def _get_message(self, timeout=None):
        
        rx_msg = Message()

        log.debug("Trying to read a msg")

        packet = capturePacket(self.socketID)

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
    

    def _put_message(self, message):
        sendPacket(self.sockedID, message)


log.debug("Loading libc with ctypes...")
libc = ctypes.cdll.LoadLibrary("libc.so.6")

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
    _fields_ = [("ifr_name", ctypes.c_wchar_p),
                ("ifr_ifindex", ctypes.c_int)]


# See /usr/include/linux/can.h for original struct
#
# The data field actually only contains 8 bytes of data, not 11. 
# The linux socketcan module aligns the start of the data to an 8 byte 
# boundary, so there are 3 empty bytes between the DLC and the data. 
#
# I couldn't find a similar function in Python that did this, so am 
# saving the three empty bytes as part of the data, and getting rid 
# of them later. See the capturePacket function further down for this. 
class CAN_FRAME(ctypes.Structure):
    _fields_ = [("can_id", ctypes.c_uint32, 32),
                ("can_dlc", ctypes.c_uint8, 8),
                ("data", (ctypes.c_uint8)*11)]


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
    log.debug('Binding socket with id {}'.format(socketID))
    socketID = ctypes.c_int(socketID)
    
    ifr = IFREQ()
    ifr.ifr_name = channel_name
    log.debug('calling ioctl SIOCGIFINDEX')
    # ifr.ifr_ifindex gets filled with that device's index
    libc.ioctl(socketID, SIOCGIFINDEX, ctypes.byref(ifr))
    log.info('ifr.ifr_ifindex: {}'.format(ifr.ifr_ifindex))
    
    # select the CAN interface and bind the socket to it
    addr = SOCKADDR_CAN(AF_CAN, ifr.ifr_ifindex)

    error = libc.bind(socketID, ctypes.byref(addr), ctypes.sizeof(addr))
    log.debug('bind returned: {}'.format(error))
    
    return error

def sendPacket(socketID, message):
    raise NotImplementedError()
    # TODO
    frame = CAN_FRAME()
    frame.can_id = 0x123
    frame.data = "foo"
    frame.can_dlc = len(frame.data)
    
    bytes_sent = libc.write(socketID, ctypes.byref(frame), ctypes.sizeof(frame))
    
    return bytes_sent

def capturePacket(socketID):
    """
    Captures a packet of data from the given socket.


    :param int socketID:
        The socket to read from

    :return:
        A dictionary with the following keys:
        +-----------+----------------------------+
        | 'CAN ID'  |int                         |
        +-----------+----------------------------+
        | 'DLC'     |int                         |
        +-----------+----------------------------+
        | 'Data'    |list                        |
        +-----------+----------------------------+
        |'Timestamp'| float                      |
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

    # TODO WHAT?
    # The first 3 elements in the data array are discarded (as they are 
    # empty) and the rest (actual data) saved into a list. 
    data = []
    for i in range(3, frame.can_dlc + 3):
        data.append(frame.data[i])

    packet['Data'] = data

    timestamp = time.tv_sec + (time.tv_usec / 1000000)
    
    packet['Timestamp'] = timestamp

    return packet


if __name__ == "__main__":
    socket_id = createSocket(CAN_RAW)
    print("Created socket (id = {})".format(socket_id))
    print(bindSocket(socket_id))
    

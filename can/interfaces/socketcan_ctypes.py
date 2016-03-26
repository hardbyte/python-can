from __future__ import print_function
import sys
import ctypes
import logging
import select

from ctypes.util import find_library

import can
from can.interfaces.socketcan_constants import *  # CAN_RAW
from can.bus import BusABC
from can.message import Message
from can.broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC

# Set up logging
log = logging.getLogger('can.socketcan.ctypes')
log.info("Loading socketcan ctypes backend")


class SocketscanCtypes_Bus(BusABC):

    """
    An implementation of the :class:`can.bus.BusABC` for SocketCAN using :mod:`ctypes`.
    """
    channel_info = "ctypes socketcan channel"

    def __init__(self,
                 channel=can.rc['channel'],
                 receive_own_messages=False,
                 *args, **kwargs):
        """
        :param str channel:
            The can interface name with which to create this bus. An example channel
            would be 'vcan0'.
        """

        self.socket = createSocket()

        log.debug("Result of createSocket was %d", self.socket)
        error = bindSocket(self.socket, channel)

        if receive_own_messages:
            error1 = recv_own_msgs(self.socket)

        super(SocketscanCtypes_Bus, self).__init__(*args, **kwargs)

    def recv(self, timeout=None):

        log.debug("Trying to read a msg")

        if timeout is None or len(select.select([self.socket],
                                                [], [], timeout)[0]) > 0:
            packet = capturePacket(self.socket)
        else:
            # socket wasn't readable or timeout occurred
            return None

        log.debug("Receiving a message")

        arbitration_id = packet['CAN ID'] & MSK_ARBID

        # Flags: EXT, RTR, ERR
        flags = (packet['CAN ID'] & MSK_FLAGS) >> 29

        rx_msg = Message(
            timestamp=packet['Timestamp'],
            is_remote_frame=bool(flags & SKT_RTRFLG),
            extended_id=bool(flags & EXTFLG),
            is_error_frame=bool(flags & SKT_ERRFLG),
            arbitration_id=arbitration_id,
            dlc=packet['DLC'],
            data=packet['Data']
        )

        return rx_msg

    def send(self, msg):
        return sendPacket(self.socket, msg)


log.debug("Loading libc with ctypes...")
libc = ctypes.cdll.LoadLibrary(find_library("c"))

start_sec = 0
start_usec = 0
SEC_USEC = 1000000


class SOCKADDR(ctypes.Structure):
    # See /usr/include/i386-linux-gnu/bits/socket.h for original struct
    _fields_ = [("sa_family", ctypes.c_uint16),
                ("sa_data", (ctypes.c_char)*14)]


class TP(ctypes.Structure):
    # This struct is only used within the SOCKADDR_CAN struct
    _fields_ = [("rx_id", ctypes.c_uint32),
                ("tx_id", ctypes.c_uint32)]


class ADDR_INFO(ctypes.Union):
    # This struct is only used within the SOCKADDR_CAN struct
    # This union is to future proof for future can address information
    _fields_ = [("tp", TP)]


class SOCKADDR_CAN(ctypes.Structure):
    # See /usr/include/linux/can.h for original struct
    _fields_ = [("can_family", ctypes.c_uint16),
                ("can_ifindex", ctypes.c_int),
                ("can_addr", ADDR_INFO)]


class IFREQ(ctypes.Structure):
    # The two fields in this struct were originally unions.
    # See /usr/include/net/if.h for original struct
    _fields_ = [("ifr_name", ctypes.c_char*16),
                ("ifr_ifindex", ctypes.c_int)]


class CAN_FRAME(ctypes.Structure):
    # See /usr/include/linux/can.h for original struct
    # The 32bit can id is directly followed by the 8bit data link count
    # The data field is aligned on an 8 byte boundary, hence the padding.
    # Aligns the data field to an 8 byte boundary
    _fields_ = [("can_id", ctypes.c_uint32),
                ("can_dlc", ctypes.c_uint8),
                ("padding", ctypes.c_ubyte * 3),
                ("data", ctypes.c_uint8 * 8)
                ]


class TIME_VALUE(ctypes.Structure):
    # See usr/include/linux/time.h for original struct
    _fields_ = [("tv_sec", ctypes.c_ulong),
                ("tv_usec", ctypes.c_ulong)]


class BCM_HEADER(ctypes.Structure):
    # See usr/include/linux/can/bcm.h for original struct
    _fields_ = [
        ("opcode", ctypes.c_uint32),
        ("flags", ctypes.c_uint32),
        ("count", ctypes.c_uint32),
        ("ival1", TIME_VALUE),
        ("ival2", TIME_VALUE),
        ("can_id", ctypes.c_uint32),
        ("nframes", ctypes.c_uint32),
        ("frames", CAN_FRAME)
    ]


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
        socketID = -1

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
    log.debug('Binding socket with id %d to channel %s', socketID, channel_name)
    socketID = ctypes.c_int(socketID)

    ifr = IFREQ()
    ifr.ifr_name = channel_name.encode('ascii')
    log.debug('calling ioctl SIOCGIFINDEX')
    # ifr.ifr_ifindex gets filled with that device's index
    libc.ioctl(socketID, SIOCGIFINDEX, ctypes.byref(ifr))
    log.info('ifr.ifr_ifindex: %d', ifr.ifr_ifindex)

    # select the CAN interface and bind the socket to it
    addr = SOCKADDR_CAN(AF_CAN, ifr.ifr_ifindex)

    error = libc.bind(socketID, ctypes.byref(addr), ctypes.sizeof(addr))

    if error < 0:
        log.error("Couldn't bind socket")
    log.debug('bind returned: %d', error)

    return error


def connectSocket(socketID, channel_name):
    """Connects the given socket to the given interface.

    :param int socketID:
        The ID of the socket to be bound

    :param str channel_name:
        The interface name to find and bind.

    :return The error code from the bind call.
    """
    log.debug('Connecting socket with id %d to channel %s', socketID, channel_name)
    socketID = ctypes.c_int(socketID)

    ifr = IFREQ()
    ifr.ifr_name = channel_name.encode('ascii')
    log.debug('calling ioctl SIOCGIFINDEX')
    # ifr.ifr_ifindex gets filled with that device's index
    libc.ioctl(socketID, SIOCGIFINDEX, ctypes.byref(ifr))
    log.info('ifr.ifr_ifindex: %d', ifr.ifr_ifindex)

    # select the CAN interface and bind the socket to it
    addr = SOCKADDR_CAN(AF_CAN, ifr.ifr_ifindex)

    error = libc.connect(socketID, ctypes.byref(addr), ctypes.sizeof(addr))

    if error < 0:
        log.error("Couldn't connect socket")
    log.debug('connect returned: %d', error)

    return error


def recv_own_msgs(socket_id):
    setting = ctypes.c_int(1)
    error = libc.setsockopt(socket_id, SOL_CAN_RAW, CAN_RAW_RECV_OWN_MSGS, ctypes.byref(setting), ctypes.sizeof(setting))

    if error < 0:
        log.error("Couldn't set recv own msgs")

    return error


def _build_can_frame(message):
    log.debug("Packing a can frame")
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
    log.debug("Data: %s", message.data)
    log.debug("Type: %s", type(message.data))

    # TODO need to understand the extended frame format
    frame = CAN_FRAME()
    frame.can_id = arbitration_id
    frame.can_dlc = len(message.data)

    frame.data[0:frame.can_dlc] = message.data

    log.debug("sizeof frame: %d", ctypes.sizeof(frame))
    return frame


def sendPacket(socket, message):
    frame = _build_can_frame(message)
    bytes_sent = libc.write(socket, ctypes.byref(frame), ctypes.sizeof(frame))
    if bytes_sent == -1:
        logging.debug("Error sending frame :-/")

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
    bytes_read = libc.read(socketID, ctypes.byref(frame), ctypes.sizeof(frame))

    # Fetching the timestamp
    error = libc.ioctl(socketID, SIOCGSTAMP, ctypes.byref(time))

    packet['CAN ID'] = frame.can_id
    packet['DLC'] = frame.can_dlc
    packet["Data"] = [frame.data[i] for i in range(frame.can_dlc)]

    timestamp = time.tv_sec + (time.tv_usec / 1000000.0)

    packet['Timestamp'] = timestamp

    return packet


def _create_bcm_frame(opcode, flags, count, ival1_seconds, ival1_usec, ival2_seconds, ival2_usec, can_id, nframes, msg_frame):

    frame = BCM_HEADER()
    frame.opcode = opcode
    frame.flags = flags

    frame.count = count
    frame.ival1.tv_sec = ival1_seconds
    frame.ival1.tv_usec = ival1_usec

    frame.ival2.tv_sec = ival2_seconds
    frame.ival2.tv_usec = ival2_usec
    frame.can_id = can_id
    frame.nframes = nframes

    frame.frames = msg_frame

    return frame


class SocketCanCtypesBCMBase(object):

    """Mixin to add a BCM socket"""

    def __init__(self, channel, *args, **kwargs):
        log.debug("Creating bcm socket on channel '%s'", channel)
        # Set up the bcm socket using ctypes
        self.bcm_socket = createSocket(protocol=CAN_BCM)
        log.debug("Created bcm socket (un-connected fd=%d)", self.bcm_socket)
        connectSocket(self.bcm_socket, channel)
        log.debug("Connected bcm socket")
        super(SocketCanCtypesBCMBase, self).__init__(channel, *args, **kwargs)


class CyclicSendTask(SocketCanCtypesBCMBase, CyclicSendTaskABC):

    def __init__(self, channel, message, period):
        """

        :param channel: The name of the CAN channel to connect to.
        :param message: The message to be sent periodically.
        :param period: The rate in seconds at which to send the message.
        """
        super(CyclicSendTask, self).__init__(channel, message, period)
        self.message = message
        # Send the bcm message with opcode TX_SETUP to start the cyclic transmit
        self._tx_setup()

    def _tx_setup(self):
        message = self.message
        # Create a low level packed frame to pass to the kernel
        msg_frame = _build_can_frame(message)
        frame = _create_bcm_frame(opcode=CAN_BCM_TX_SETUP,
                                  flags=SETTIMER | STARTTIMER,
                                  count=0,
                                  ival1_seconds=0,
                                  ival1_usec=0,
                                  ival2_seconds=int(self.period),
                                  ival2_usec=int(1e6 * (self.period - int(self.period))),
                                  can_id=message.arbitration_id,
                                  nframes=1,
                                  msg_frame=msg_frame)

        log.info("Sending BCM TX_SETUP command")
        bytes_sent = libc.send(self.bcm_socket, ctypes.byref(frame), ctypes.sizeof(frame))
        if bytes_sent == -1:
            logging.debug("Error sending frame :-/")

    def start(self):
        self._tx_setup()

    def stop(self):
        """Send a TX_DELETE message to cancel this task.

        This will delete the entry for the transmission of the CAN-message
        with the specified can_id CAN identifier. The message length for the command
        TX_DELETE is {[bcm_msg_head]} (only the header).
        """

        frame = _create_bcm_frame(
            opcode=CAN_BCM_TX_DELETE,
            flags=0,
            count=0,
            ival1_seconds=0,
            ival1_usec=0,
            ival2_seconds=0,
            ival2_usec=0,
            can_id=self.can_id,
            nframes=0,
            msg_frame=CAN_FRAME()
        )

        bytes_sent = libc.send(self.bcm_socket, ctypes.byref(frame), ctypes.sizeof(frame))
        if bytes_sent == -1:
            logging.debug("Error sending frame to stop cyclic message:-/")

    def modify_data(self, message):
        """Update the contents of this periodically sent message.
        """
        assert message.arbitration_id == self.can_id, "You cannot modify the can identifier"
        self.message = message
        self._tx_setup()


class MultiRateCyclicSendTask(CyclicSendTask):

    """Exposes more of the full power of the TX_SETUP opcode.

    Transmits a message `count` times at `initial_period` then
    continues to transmit message at `subsequent_period`.
    """

    def __init__(self, channel, message, count, initial_period, subsequent_period):
        super(MultiRateCyclicSendTask, self).__init__(channel, message, subsequent_period)

        msg_frame = _build_can_frame(message)

        frame = _create_bcm_frame(opcode=CAN_BCM_TX_SETUP,
                                  flags=SETTIMER | STARTTIMER,
                                  count=count,
                                  ival1_seconds=int(initial_period),
                                  ival1_usec=int(1e6 * (initial_period - int(initial_period))),
                                  ival2_seconds=int(subsequent_period),
                                  ival2_usec=int(1e6 * (subsequent_period - int(subsequent_period))),
                                  can_id=message.arbitration_id,
                                  nframes=1,
                                  msg_frame=msg_frame)

        log.info("Sending BCM TX_SETUP command")
        bytes_sent = libc.send(self.bcm_socket, ctypes.byref(frame), ctypes.sizeof(frame))
        if bytes_sent == -1:
            logging.debug("Error sending frame :-/")

if __name__ == "__main__":
    socket_id = createSocket(CAN_RAW)
    print("Created socket (id = {})".format(socket_id))
    print(bindSocket(socket_id))

import sys
import time
import logging
from ctypes import *

from can import CanError, BusABC, Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

NC_SUCCESS = 0
NC_ERR_TIMEOUT = 1

# NCTYPE_OPCODE values
NC_OP_START = 0x80000001
NC_OP_STOP = 0x80000002
NC_OP_RESET = 0x8000003

# NCTYPE State
NC_ST_READ_AVAIL = 0x00000001
NC_ST_WRITE_SUCCESS = 0x00000002
NC_ST_ERROR = 0x00000010
NC_ST_WARNING = 0x00000020

NC_ATTR_BAUD_RATE = 0x80000007
NC_ATTR_START_ON_OPEN = 0x80000006
NC_ATTR_READ_Q_LEN = 0x80000013
NC_ATTR_WRITE_Q_LEN = 0x80000014
NC_ATTR_CAN_COMP_STD = 0x80010001
NC_ATTR_CAN_MASK_STD = 0x80010002
NC_CAN_MASK_STD_DONTCARE = 0x00000000
NC_ATTR_CAN_COMP_XTD = 0x80010003
NC_ATTR_CAN_MASK_XTD = 0x80010004
NC_CAN_MASK_XTD_DONTCARE = 0x00000000
NC_FL_CAN_ARBID_XTD = 0x20000000


class RxMessageStruct(Structure):
    _pack_ = 1
    _fields_ = [
        ("timestamp", c_ulonglong),
        ("arb_id", c_ulong),
        ("is_remote", c_ubyte),
        ("dlc", c_ubyte),
        ("data", c_ubyte*8),
    ]

class TxMessageStruct(Structure):
    _fields_ = [
        ("arb_id", c_ulong),
        ("is_remote", c_ubyte),
        ("dlc", c_ubyte),
        ("data", c_ubyte*8),
    ]


def check_status(result, function, arguments):
    if result.value != NC_SUCCESS:
        raise NicanError(function, result, arguments)
    return result

try:
    nican = windll.LoadLibrary("nican")
except OSError:
    logger.error("NI-CAN drivers could not be loaded")
else:
    nican.ncConfig.argtypes = [c_char_p, c_void_p, c_void_p]
    nican.ncConfig.errcheck = check_status
    nican.ncOpenObject.argtypes = [c_char_p, c_void_p]
    nican.ncOpenObject.errcheck = check_status
    nican.ncCloseObject.errcheck = check_status
    nican.ncAction.errcheck = check_status
    nican.ncRead.errcheck = check_status
    nican.ncWrite.errcheck = check_status
    nican.ncWaitForState.argtypes = [c_ulong, c_ulong, c_ulong, c_void_p]
    nican.ncWaitForState.errcheck = check_status
    nican.ncStatusToString.argtypes = [c_int, c_uint, c_char_p]


class NicanBus(BusABC):

    def __init__(self, channel, **kwargs):
        self.channel_info = "NI-CAN: " + channel

        config = {
            NC_ATTR_START_ON_OPEN: 1,
            NC_ATTR_READ_Q_LEN: kwargs.get("read_queue", 150),
            NC_ATTR_WRITE_Q_LEN: kwargs.get("write_queue", 2),
            NC_ATTR_CAN_COMP_STD: 0,
            NC_ATTR_CAN_MASK_STD: 0,
            NC_ATTR_CAN_COMP_XTD: 0,
            NC_ATTR_CAN_MASK_XTD: 0,
        }
        if "bitrate" in kwargs:
            config[NC_ATTR_BAUD_RATE] = kwargs["bitrate"]
        AttrList = c_ulong * len(config)
        nican.ncConfig(channel,
                       AttrList(*config.keys()),
                       AttrList(*config.values()))
        self.handle = c_ulong()
        nican.ncOpenObject(channel, byref(self.handle))

    def recv(self, timeout=None):
        state = c_ulong()
        timeout = 0xFFFFFFFF if timeout is None else int(timeout * 1000)
        try:
            nican.ncWaitForState(self.handle, NC_ST_READ_AVAIL,
                timeout, byref(state))
        except NicanError as e:
            if e.error_code == NC_ERR_TIMEOUT:
                return None
            else:
                raise

        raw_msg = RxMessageStruct()
        nican.ncRead(self.handle, sizeof(raw_msg), byref(raw_msg))
        # http://stackoverflow.com/questions/6161776/convert-windows-filetime-to-second-in-unix-linux
        timestamp = raw_msg.timestamp / 10000000.0 - 11644473600
        msg = Message(timestamp=timestamp,
                      is_remote_frame=bool(raw_msg.is_remote),
                      extended_id=bool(raw_msg.arb_id & NC_FL_CAN_ARBID_XTD),
                      arbitration_id=raw_msg.arb_id & 0x1FFFFFFF,
                      dlc=raw_msg.dlc,
                      data=raw_msg.data[:raw_msg.dlc])
        return msg

    def send(self, msg):
        arb_id = msg.arbitration_id
        if msg.id_type:
            arb_id |= NC_FL_CAN_ARBID_XTD
        raw_msg = TxMessageStruct(arb_id,
                                  bool(msg.is_remote_frame),
                                  msg.dlc,
                                  (c_ubyte*8)(*msg.data))
        nican.ncWrite(self.handle, sizeof(raw_msg), byref(raw_msg))
        state = c_ulong()
        nican.ncWaitForState(self.handle,
                             NC_ST_WRITE_SUCCESS | NC_ST_WARNING | NC_ST_ERROR,
                             10,
                             byref(state))

    def shutdown(self):
        nican.ncCloseObject(self.handle)


class NicanError(CanError):

    def __init__(self, function, error_code, arguments):
        super(CANLIBError, self).__init__()
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "Function %s failed - %s" % (self.function.__name__,
                                            self.get_error_message())

    def get_error_message(self):
        errmsg = create_string_buffer(128)
        nican.ncStatusToString(self.error_code, len(errmsg), errmsg)
        return errmsg.value.decode("ascii")

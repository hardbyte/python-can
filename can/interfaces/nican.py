"""
NI-CAN interface module.

http://www.ni.com/pdf/manuals/370289c.pdf
https://github.com/buendiya/NicanPython
"""

import sys
import time
import logging
import ctypes

from can import CanError, BusABC, Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

NC_SUCCESS = 0
NC_ERR_TIMEOUT = 1

# NCTYPE_OPCODE values
NC_OP_START = 0x80000001
NC_OP_STOP = 0x80000002
NC_OP_RESET = 0x8000003

NC_FRMTYPE_REMOTE = 1
NC_FRMTYPE_COMM_ERR = 2
TIMEOUT_ERROR_CODE = -1074388991

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


CanData = ctypes.c_ubyte * 8

class RxMessageStruct(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timestamp", ctypes.c_ulonglong),
        ("arb_id", ctypes.c_ulong),
        ("frame_type", ctypes.c_ubyte),
        ("dlc", ctypes.c_ubyte),
        ("data", CanData),
    ]

class TxMessageStruct(ctypes.Structure):
    _fields_ = [
        ("arb_id", ctypes.c_ulong),
        ("is_remote", ctypes.c_ubyte),
        ("dlc", ctypes.c_ubyte),
        ("data", CanData),
    ]


def check_status(result, function, arguments):
    if result == NC_SUCCESS:
        pass
    elif result > 0:
        print(get_error_message(result))
    elif result < 0:
        raise NicanError(function, result, arguments)
    return result


def get_error_message(status_code):
    errmsg = ctypes.create_string_buffer(1024)
    nican.ncStatusToString(status_code, len(errmsg), errmsg)
    return errmsg.value.decode("ascii")


try:
    nican = ctypes.windll.LoadLibrary("nican")
except OSError as e:
    logger.error(e)
else:
    nican.ncConfig.argtypes = [
        ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
    nican.ncConfig.errcheck = check_status
    nican.ncOpenObject.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
    nican.ncOpenObject.errcheck = check_status
    nican.ncCloseObject.errcheck = check_status
    nican.ncAction.errcheck = check_status
    nican.ncRead.errcheck = check_status
    nican.ncWrite.errcheck = check_status
    nican.ncWaitForState.argtypes = [
        ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
    nican.ncWaitForState.errcheck = check_status
    nican.ncStatusToString.argtypes = [
        ctypes.c_int, ctypes.c_uint, ctypes.c_char_p]


class NicanBus(BusABC):

    def __init__(self, channel, **kwargs):
        self.channel_info = "NI-CAN: " + channel
        if not isinstance(channel, bytes):
            channel = channel.encode()

        config = {
            NC_ATTR_START_ON_OPEN: 1,
            NC_ATTR_CAN_COMP_STD: 0,
            NC_ATTR_CAN_MASK_STD: 0,
            NC_ATTR_CAN_COMP_XTD: 0,
            NC_ATTR_CAN_MASK_XTD: 0,
        }
        can_filters = kwargs.get("can_filters")
        if not can_filters:
            logger.info("Filtering has been disabled")
        elif len(can_filters) == 1:
            can_id = can_filters[0]['can_id']
            can_mask = can_filters[0]['can_mask']
            logger.info("Filtering on ID 0x%X, mask 0x%X", can_id, can_mask)
            config[NC_ATTR_CAN_COMP_STD] = can_id
            config[NC_ATTR_CAN_MASK_STD] = can_mask
            config[NC_ATTR_CAN_COMP_XTD] = can_id
            config[NC_ATTR_CAN_MASK_XTD] = can_mask
        else:
            logger.warning("Only one filter is supported")

        if "bitrate" in kwargs:
            config[NC_ATTR_BAUD_RATE] = kwargs["bitrate"]
        config[NC_ATTR_READ_Q_LEN] = kwargs.get("read_queue", 150)
        config[NC_ATTR_WRITE_Q_LEN] = kwargs.get("write_queue", 2)
        AttrList = ctypes.c_ulong * len(config)
        nican.ncConfig(channel,
                       len(config),
                       ctypes.byref(AttrList(*config.keys())),
                       ctypes.byref(AttrList(*config.values())))
        self.handle = ctypes.c_ulong()
        nican.ncOpenObject(channel, ctypes.byref(self.handle))

    def recv(self, timeout=None):
        state = ctypes.c_ulong()
        timeout = 0xFFFFFFFF if timeout is None else int(timeout * 1000)
        try:
            nican.ncWaitForState(
                self.handle, NC_ST_READ_AVAIL, timeout, ctypes.byref(state))
        except NicanError as e:
            if e.error_code == TIMEOUT_ERROR_CODE:
                return None
            else:
                raise

        raw_msg = RxMessageStruct()
        nican.ncRead(self.handle, ctypes.sizeof(raw_msg), ctypes.byref(raw_msg))
        # http://stackoverflow.com/questions/6161776/convert-windows-filetime-to-second-in-unix-linux
        timestamp = raw_msg.timestamp / 10000000.0 - 11644473600
        frame_type = raw_msg.frame_type
        arb_id = raw_msg.arb_id
        dlc = raw_msg.dlc
        msg = Message(timestamp=timestamp,
                      is_remote_frame=bool(frame_type & NC_FRMTYPE_REMOTE),
                      is_error_frame=bool(frame_type & NC_FRMTYPE_COMM_ERR),
                      extended_id=bool(arb_id & NC_FL_CAN_ARBID_XTD),
                      arbitration_id=arb_id & 0x1FFFFFFF,
                      dlc=dlc,
                      data=raw_msg.data[:dlc])
        return msg

    def send(self, msg):
        arb_id = msg.arbitration_id
        if msg.id_type:
            arb_id |= NC_FL_CAN_ARBID_XTD
        raw_msg = TxMessageStruct(arb_id,
                                  bool(msg.is_remote_frame),
                                  msg.dlc,
                                  CanData(*msg.data))
        nican.ncWrite(
            self.handle, ctypes.sizeof(raw_msg), ctypes.byref(raw_msg))
        state = ctypes.c_ulong()
        nican.ncWaitForState(
            self.handle, NC_ST_WRITE_SUCCESS, 10, ctypes.byref(state))

    def shutdown(self):
        nican.ncCloseObject(self.handle)


class NicanError(CanError):

    def __init__(self, function, error_code, arguments):
        super(NicanError, self).__init__()
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "Function %s failed:\n%s" % (
            self.function.__name__, get_error_message(self.error_code))

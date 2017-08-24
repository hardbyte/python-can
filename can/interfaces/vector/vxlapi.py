# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems
Authors: Julien Grave <grave.jul@gmail.com>, Christian Sandberg
"""
# Import Standard Python Modules
# ==============================
import ctypes
import logging
import platform
from .exceptions import VectorError

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Vector XL API Definitions
# =========================
# Load Windows DLL
DLL_NAME = 'vxlapi64' if platform.architecture()[0] == '64bit' else 'vxlapi'
_xlapi_dll = ctypes.windll.LoadLibrary(DLL_NAME)

XL_BUS_TYPE_CAN = 0x00000001

XL_ERR_QUEUE_IS_EMPTY = 10

XL_RECEIVE_MSG = 1
XL_TRANSMIT_MSG = 10

XL_CAN_EXT_MSG_ID = 0x80000000
XL_CAN_MSG_FLAG_ERROR_FRAME = 0x01
XL_CAN_MSG_FLAG_REMOTE_FRAME = 0x10

XL_CAN_STD = 1
XL_CAN_EXT = 2

XLuint64 = ctypes.c_ulonglong
XLaccess = XLuint64

MAX_MSG_LEN = 8

# current version
XL_INTERFACE_VERSION = 3

# structure for XL_RECEIVE_MSG, XL_TRANSMIT_MSG
class s_xl_can_msg(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ulong), ('flags', ctypes.c_ushort),
                ('dlc', ctypes.c_ushort), ('res1', XLuint64),
                ('data', ctypes.c_ubyte * MAX_MSG_LEN), ('res2', XLuint64)]

# BASIC bus message structure
class s_xl_tag_data(ctypes.Union):
    _fields_ = [('msg', s_xl_can_msg)]


XLeventTag = ctypes.c_ubyte

class XLevent(ctypes.Structure):
    _fields_ = [('tag', XLeventTag), ('chanIndex', ctypes.c_ubyte),
                ('transId', ctypes.c_ushort), ('portHandle', ctypes.c_ushort),
                ('flags', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte),
                ('timeStamp', XLuint64), ('tagData', s_xl_tag_data)]

# driver status
XLstatus = ctypes.c_short

# porthandle
XL_INVALID_PORTHANDLE = (-1)
XLportHandle = ctypes.c_long


def check_status(result, function, arguments):
    if result > 0:
        raise VectorError(result, xlGetErrorString(result).decode())
    return result


xlOpenDriver = _xlapi_dll.xlOpenDriver
xlOpenDriver.argtypes = []
xlOpenDriver.restype = XLstatus
xlOpenDriver.errcheck = check_status

xlCloseDriver = _xlapi_dll.xlCloseDriver
xlCloseDriver.argtypes = []
xlCloseDriver.restype = XLstatus
xlCloseDriver.errcheck = check_status

xlGetApplConfig = _xlapi_dll.xlGetApplConfig
xlGetApplConfig.argtypes = [
    ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint
]
xlGetApplConfig.restype = XLstatus
xlGetApplConfig.errcheck = check_status

xlGetChannelIndex = _xlapi_dll.xlGetChannelIndex
xlGetChannelIndex.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelIndex.restype = ctypes.c_int

xlGetChannelMask = _xlapi_dll.xlGetChannelMask
xlGetChannelMask.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelMask.restype = XLaccess

xlOpenPort = _xlapi_dll.xlOpenPort
xlOpenPort.argtypes = [
    ctypes.POINTER(XLportHandle), ctypes.c_char_p, XLaccess,
    ctypes.POINTER(XLaccess), ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
]
xlOpenPort.restype = XLstatus
xlOpenPort.errcheck = check_status

xlGetSyncTime = _xlapi_dll.xlGetSyncTime
xlGetSyncTime.argtypes = [XLportHandle, ctypes.POINTER(XLuint64)]
xlGetSyncTime.restype = XLstatus
xlGetSyncTime.errcheck = check_status

xlClosePort = _xlapi_dll.xlClosePort
xlClosePort.argtypes = [XLportHandle]
xlClosePort.restype = XLstatus
xlClosePort.errcheck = check_status

xlActivateChannel = _xlapi_dll.xlActivateChannel
xlActivateChannel.argtypes = [
    XLportHandle, XLaccess, ctypes.c_uint, ctypes.c_uint
]
xlActivateChannel.restype = XLstatus
xlActivateChannel.errcheck = check_status

xlDeactivateChannel = _xlapi_dll.xlDeactivateChannel
xlDeactivateChannel.argtypes = [XLportHandle, XLaccess]
xlDeactivateChannel.restype = XLstatus
xlDeactivateChannel.errcheck = check_status

xlReceive = _xlapi_dll.xlReceive
xlReceive.argtypes = [
    XLportHandle, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLevent)
]
xlReceive.restype = XLstatus
xlReceive.errcheck = check_status

xlGetErrorString = _xlapi_dll.xlGetErrorString
xlGetErrorString.argtypes = [XLstatus]
xlGetErrorString.restype = ctypes.c_char_p

xlCanSetChannelBitrate = _xlapi_dll.xlCanSetChannelBitrate
xlCanSetChannelBitrate.argtypes = [XLportHandle, XLaccess, ctypes.c_ulong]
xlCanSetChannelBitrate.restype = XLstatus
xlCanSetChannelBitrate.errcheck = check_status

xlCanTransmit = _xlapi_dll.xlCanTransmit
xlCanTransmit.argtypes = [
    XLportHandle, XLaccess, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLevent)
]
xlCanTransmit.restype = XLstatus
xlCanTransmit.errcheck = check_status

xlCanFlushTransmitQueue = _xlapi_dll.xlCanFlushTransmitQueue
xlCanFlushTransmitQueue.argtypes = [XLportHandle, XLaccess]
xlCanFlushTransmitQueue.restype = XLstatus
xlCanFlushTransmitQueue.errcheck = check_status

xlCanSetChannelAcceptance = _xlapi_dll.xlCanSetChannelAcceptance
xlCanSetChannelAcceptance.argtypes = [
    XLportHandle, XLaccess, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_uint]
xlCanSetChannelAcceptance.restype = XLstatus
xlCanSetChannelAcceptance.errcheck = check_status

xlCanResetAcceptance = _xlapi_dll.xlCanResetAcceptance
xlCanResetAcceptance.argtypes = [XLportHandle, XLaccess, ctypes.c_uint]
xlCanResetAcceptance.restype = XLstatus
xlCanResetAcceptance.errcheck = check_status

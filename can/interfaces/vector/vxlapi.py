#!/usr/bin/env python
# coding: utf-8

"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems.

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
XL_ERR_HW_NOT_PRESENT = 129

XL_RECEIVE_MSG = 1
XL_CAN_EV_TAG_RX_OK = 1024
XL_CAN_EV_TAG_TX_OK = 1028
XL_TRANSMIT_MSG = 10
XL_CAN_EV_TAG_TX_MSG = 1088

XL_CAN_EXT_MSG_ID = 0x80000000
XL_CAN_MSG_FLAG_ERROR_FRAME = 0x01
XL_CAN_MSG_FLAG_REMOTE_FRAME = 0x10
XL_CAN_MSG_FLAG_TX_COMPLETED = 0x40

XL_CAN_TXMSG_FLAG_EDL = 0x0001
XL_CAN_TXMSG_FLAG_BRS = 0x0002
XL_CAN_TXMSG_FLAG_RTR = 0x0010
XL_CAN_RXMSG_FLAG_EDL = 0x0001
XL_CAN_RXMSG_FLAG_BRS = 0x0002
XL_CAN_RXMSG_FLAG_ESI = 0x0004
XL_CAN_RXMSG_FLAG_RTR = 0x0010
XL_CAN_RXMSG_FLAG_EF = 0x0200 

XL_CAN_STD = 1
XL_CAN_EXT = 2

XLuint64 = ctypes.c_int64
XLaccess = XLuint64
XLhandle = ctypes.c_void_p

MAX_MSG_LEN = 8

XL_CAN_MAX_DATA_LEN = 64

# current version
XL_INTERFACE_VERSION = 3
XL_INTERFACE_VERSION_V4 = 4

XL_CHANNEL_FLAG_CANFD_ISO_SUPPORT = 0x80000000

# structure for XL_RECEIVE_MSG, XL_TRANSMIT_MSG
class s_xl_can_msg(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ulong), ('flags', ctypes.c_ushort),
                ('dlc', ctypes.c_ushort), ('res1', XLuint64),
                ('data', ctypes.c_ubyte * MAX_MSG_LEN), ('res2', XLuint64)]



class s_xl_can_ev_error(ctypes.Structure):
    _fields_ = [('errorCode', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte * 95)]

class s_xl_can_ev_chip_state(ctypes.Structure):
    _fields_ = [('busStatus', ctypes.c_ubyte), ('txErrorCounter', ctypes.c_ubyte),
                ('rxErrorCounter', ctypes.c_ubyte),('reserved', ctypes.c_ubyte),
                ('reserved0', ctypes.c_uint)]

class s_xl_can_ev_sync_pulse(ctypes.Structure):
    _fields_ = [('triggerSource', ctypes.c_uint), ('reserved', ctypes.c_uint),
                ('time', XLuint64)]

# BASIC bus message structure
class s_xl_tag_data(ctypes.Union):
    _fields_ = [('msg', s_xl_can_msg)]

# CAN FD messages
class s_xl_can_ev_rx_msg(ctypes.Structure):
    _fields_ = [('canId', ctypes.c_uint), ('msgFlags', ctypes.c_uint),
                ('crc', ctypes.c_uint), ('reserved1', ctypes.c_ubyte * 12),
                ('totalBitCnt', ctypes.c_ushort), ('dlc', ctypes.c_ubyte),
                ('reserved', ctypes.c_ubyte * 5), ('data', ctypes.c_ubyte * XL_CAN_MAX_DATA_LEN)]

class s_xl_can_ev_tx_request(ctypes.Structure):
    _fields_ = [('canId', ctypes.c_uint), ('msgFlags', ctypes.c_uint),
                ('dlc', ctypes.c_ubyte),('txAttemptConf', ctypes.c_ubyte),
                ('reserved', ctypes.c_ushort), ('data', ctypes.c_ubyte * XL_CAN_MAX_DATA_LEN)]

class s_xl_can_tx_msg(ctypes.Structure):
    _fields_ = [('canId', ctypes.c_uint), ('msgFlags', ctypes.c_uint),
                ('dlc', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte * 7),
                ('data', ctypes.c_ubyte * XL_CAN_MAX_DATA_LEN)]

class s_rxTagData(ctypes.Union):
    _fields_ = [('canRxOkMsg', s_xl_can_ev_rx_msg), ('canTxOkMsg', s_xl_can_ev_rx_msg),
                ('canTxRequest', s_xl_can_ev_tx_request),('canError', s_xl_can_ev_error),
                ('canChipState', s_xl_can_ev_chip_state),('canSyncPulse', s_xl_can_ev_sync_pulse)]

class s_txTagData(ctypes.Union):
    _fields_ = [('canMsg', s_xl_can_tx_msg)]

# BASIC events				
XLeventTag = ctypes.c_ubyte

class XLevent(ctypes.Structure):
    _fields_ = [('tag', XLeventTag), ('chanIndex', ctypes.c_ubyte),
                ('transId', ctypes.c_ushort), ('portHandle', ctypes.c_ushort),
                ('flags', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte),
                ('timeStamp', XLuint64), ('tagData', s_xl_tag_data)]

# CAN FD events
class XLcanRxEvent(ctypes.Structure):
    _fields_ = [('size',ctypes.c_int),('tag', ctypes.c_ushort),
                ('chanIndex', ctypes.c_ubyte),('reserved', ctypes.c_ubyte),
                ('userHandle', ctypes.c_int),('flagsChip', ctypes.c_ushort),
                ('reserved0', ctypes.c_ushort),('reserved1', XLuint64),
                ('timeStamp', XLuint64),('tagData', s_rxTagData)]

class XLcanTxEvent(ctypes.Structure):
    _fields_ = [('tag', ctypes.c_ushort), ('transId', ctypes.c_ushort),
                ('chanIndex', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte * 3),
                ('tagData', s_txTagData)]

# CAN FD configuration structure
class XLcanFdConf(ctypes.Structure):
    _fields_ = [('arbitrationBitRate', ctypes.c_uint), ('sjwAbr', ctypes.c_uint),
                ('tseg1Abr', ctypes.c_uint), ('tseg2Abr', ctypes.c_uint),
                ('dataBitRate', ctypes.c_uint), ('sjwDbr', ctypes.c_uint),
                ('tseg1Dbr', ctypes.c_uint), ('tseg2Dbr', ctypes.c_uint),
                ('reserved', ctypes.c_uint * 2)]

class XLchannelConfig(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('name', ctypes.c_char * 32),
        ('hwType', ctypes.c_ubyte),
        ('hwIndex', ctypes.c_ubyte),
        ('hwChannel', ctypes.c_ubyte),
        ('transceiverType', ctypes.c_ushort),
        ('transceiverState', ctypes.c_ushort),
        ('configError', ctypes.c_ushort),
        ('channelIndex', ctypes.c_ubyte),
        ('channelMask', XLuint64),
        ('channelCapabilities', ctypes.c_uint),
        ('channelBusCapabilities', ctypes.c_uint),
        ('isOnBus', ctypes.c_ubyte),
        ('connectedBusType', ctypes.c_uint),
        ('busParams', ctypes.c_ubyte * 32),
        ('_doNotUse', ctypes.c_uint),
        ('driverVersion', ctypes.c_uint),
        ('interfaceVersion', ctypes.c_uint),
        ('raw_data', ctypes.c_uint * 10),
        ('serialNumber', ctypes.c_uint),
        ('articleNumber', ctypes.c_uint),
        ('transceiverName', ctypes.c_char * 32),
        ('specialCabFlags', ctypes.c_uint),
        ('dominantTimeout', ctypes.c_uint),
        ('dominantRecessiveDelay', ctypes.c_ubyte),
        ('recessiveDominantDelay', ctypes.c_ubyte),
        ('connectionInfo', ctypes.c_ubyte),
        ('currentlyAvailableTimestamps', ctypes.c_ubyte),
        ('minimalSupplyVoltage', ctypes.c_ushort),
        ('maximalSupplyVoltage', ctypes.c_ushort),
        ('maximalBaudrate', ctypes.c_uint),
        ('fpgaCoreCapabilities', ctypes.c_ubyte),
        ('specialDeviceStatus', ctypes.c_ubyte),
        ('channelBusActiveCapabilities', ctypes.c_ushort),
        ('breakOffset', ctypes.c_ushort),
        ('delimiterOffset', ctypes.c_ushort),
        ('reserved', ctypes.c_uint * 3)
    ]

class XLdriverConfig(ctypes.Structure):
    _fields_ = [
        ('dllVersion', ctypes.c_uint),
        ('channelCount', ctypes.c_uint),
        ('reserved', ctypes.c_uint * 10),
        ('channel', XLchannelConfig * 64)
    ]

# driver status
XLstatus = ctypes.c_short

# porthandle
XL_INVALID_PORTHANDLE = (-1)
XLportHandle = ctypes.c_long


def check_status(result, function, arguments):
    if result > 0:
        raise VectorError(result, xlGetErrorString(result).decode(), function.__name__)
    return result


xlGetDriverConfig = _xlapi_dll.xlGetDriverConfig
xlGetDriverConfig.argtypes = [ctypes.POINTER(XLdriverConfig)]
xlGetDriverConfig.restype = XLstatus
xlGetDriverConfig.errcheck = check_status

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

xlSetNotification = _xlapi_dll.xlSetNotification
xlSetNotification.argtypes = [XLportHandle, ctypes.POINTER(XLhandle),
                              ctypes.c_int]
xlSetNotification.restype = XLstatus
xlSetNotification.errcheck = check_status

xlCanSetChannelMode = _xlapi_dll.xlCanSetChannelMode
xlCanSetChannelMode.argtypes = [
    XLportHandle, XLaccess, ctypes.c_int, ctypes.c_int
]
xlCanSetChannelMode.restype = XLstatus
xlCanSetChannelMode.errcheck = check_status

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

xlCanFdSetConfiguration = _xlapi_dll.xlCanFdSetConfiguration
xlCanFdSetConfiguration.argtypes = [XLportHandle, XLaccess, ctypes.POINTER(XLcanFdConf)]
xlCanFdSetConfiguration.restype = XLstatus
xlCanFdSetConfiguration.errcheck = check_status

xlReceive = _xlapi_dll.xlReceive
xlReceive.argtypes = [
    XLportHandle, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLevent)
]
xlReceive.restype = XLstatus
xlReceive.errcheck = check_status

xlCanReceive = _xlapi_dll.xlCanReceive
xlCanReceive.argtypes = [
    XLportHandle, ctypes.POINTER(XLcanRxEvent)
]
xlCanReceive.restype = XLstatus
xlCanReceive.errcheck = check_status

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

xlCanTransmitEx = _xlapi_dll.xlCanTransmitEx
xlCanTransmitEx.argtypes = [
    XLportHandle, XLaccess, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLcanTxEvent)
]
xlCanTransmitEx.restype = XLstatus
xlCanTransmitEx.errcheck = check_status

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

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
from . import xlclass

# Load Windows DLL
DLL_NAME = "vxlapi64" if platform.architecture()[0] == "64bit" else "vxlapi"
_xlapi_dll = ctypes.windll.LoadLibrary(DLL_NAME)


# ctypes wrapping for API functions
xlGetErrorString = _xlapi_dll.xlGetErrorString
xlGetErrorString.argtypes = [xlclass.XLstatus]
xlGetErrorString.restype = ctypes.c_char_p


def check_status(result, function, arguments):
    if result > 0:
        raise VectorError(result, xlGetErrorString(result).decode(), function.__name__)
    return result


xlGetDriverConfig = _xlapi_dll.xlGetDriverConfig
xlGetDriverConfig.argtypes = [ctypes.POINTER(xlclass.XLdriverConfig)]
xlGetDriverConfig.restype = xlclass.XLstatus
xlGetDriverConfig.errcheck = check_status

xlOpenDriver = _xlapi_dll.xlOpenDriver
xlOpenDriver.argtypes = []
xlOpenDriver.restype = xlclass.XLstatus
xlOpenDriver.errcheck = check_status

xlCloseDriver = _xlapi_dll.xlCloseDriver
xlCloseDriver.argtypes = []
xlCloseDriver.restype = xlclass.XLstatus
xlCloseDriver.errcheck = check_status

xlGetApplConfig = _xlapi_dll.xlGetApplConfig
xlGetApplConfig.argtypes = [
    ctypes.c_char_p,
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint),
    ctypes.c_uint,
]
xlGetApplConfig.restype = xlclass.XLstatus
xlGetApplConfig.errcheck = check_status

xlGetChannelIndex = _xlapi_dll.xlGetChannelIndex
xlGetChannelIndex.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelIndex.restype = ctypes.c_int

xlGetChannelMask = _xlapi_dll.xlGetChannelMask
xlGetChannelMask.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelMask.restype = xlclass.XLaccess

xlOpenPort = _xlapi_dll.xlOpenPort
xlOpenPort.argtypes = [
    ctypes.POINTER(xlclass.XLportHandle),
    ctypes.c_char_p,
    xlclass.XLaccess,
    ctypes.POINTER(xlclass.XLaccess),
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
]
xlOpenPort.restype = xlclass.XLstatus
xlOpenPort.errcheck = check_status

xlGetSyncTime = _xlapi_dll.xlGetSyncTime
xlGetSyncTime.argtypes = [xlclass.XLportHandle, ctypes.POINTER(xlclass.XLuint64)]
xlGetSyncTime.restype = xlclass.XLstatus
xlGetSyncTime.errcheck = check_status

xlGetChannelTime = _xlapi_dll.xlGetChannelTime
xlGetChannelTime.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.POINTER(xlclass.XLuint64),
]
xlGetChannelTime.restype = xlclass.XLstatus
xlGetChannelTime.errcheck = check_status

xlClosePort = _xlapi_dll.xlClosePort
xlClosePort.argtypes = [xlclass.XLportHandle]
xlClosePort.restype = xlclass.XLstatus
xlClosePort.errcheck = check_status

xlSetNotification = _xlapi_dll.xlSetNotification
xlSetNotification.argtypes = [
    xlclass.XLportHandle,
    ctypes.POINTER(xlclass.XLhandle),
    ctypes.c_int,
]
xlSetNotification.restype = xlclass.XLstatus
xlSetNotification.errcheck = check_status

xlCanSetChannelMode = _xlapi_dll.xlCanSetChannelMode
xlCanSetChannelMode.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.c_int,
    ctypes.c_int,
]
xlCanSetChannelMode.restype = xlclass.XLstatus
xlCanSetChannelMode.errcheck = check_status

xlActivateChannel = _xlapi_dll.xlActivateChannel
xlActivateChannel.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.c_uint,
    ctypes.c_uint,
]
xlActivateChannel.restype = xlclass.XLstatus
xlActivateChannel.errcheck = check_status

xlDeactivateChannel = _xlapi_dll.xlDeactivateChannel
xlDeactivateChannel.argtypes = [xlclass.XLportHandle, xlclass.XLaccess]
xlDeactivateChannel.restype = xlclass.XLstatus
xlDeactivateChannel.errcheck = check_status

xlCanFdSetConfiguration = _xlapi_dll.xlCanFdSetConfiguration
xlCanFdSetConfiguration.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.POINTER(xlclass.XLcanFdConf),
]
xlCanFdSetConfiguration.restype = xlclass.XLstatus
xlCanFdSetConfiguration.errcheck = check_status

xlReceive = _xlapi_dll.xlReceive
xlReceive.argtypes = [
    xlclass.XLportHandle,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(xlclass.XLevent),
]
xlReceive.restype = xlclass.XLstatus
xlReceive.errcheck = check_status

xlCanReceive = _xlapi_dll.xlCanReceive
xlCanReceive.argtypes = [xlclass.XLportHandle, ctypes.POINTER(xlclass.XLcanRxEvent)]
xlCanReceive.restype = xlclass.XLstatus
xlCanReceive.errcheck = check_status

xlCanSetChannelBitrate = _xlapi_dll.xlCanSetChannelBitrate
xlCanSetChannelBitrate.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.c_ulong,
]
xlCanSetChannelBitrate.restype = xlclass.XLstatus
xlCanSetChannelBitrate.errcheck = check_status

xlCanSetChannelParams = _xlapi_dll.xlCanSetChannelParams
xlCanSetChannelParams.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.POINTER(xlclass.XLchipParams),
]
xlCanSetChannelParams.restype = xlclass.XLstatus
xlCanSetChannelParams.errcheck = check_status

xlCanTransmit = _xlapi_dll.xlCanTransmit
xlCanTransmit.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(xlclass.XLevent),
]
xlCanTransmit.restype = xlclass.XLstatus
xlCanTransmit.errcheck = check_status

xlCanTransmitEx = _xlapi_dll.xlCanTransmitEx
xlCanTransmitEx.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(xlclass.XLcanTxEvent),
]
xlCanTransmitEx.restype = xlclass.XLstatus
xlCanTransmitEx.errcheck = check_status

xlCanFlushTransmitQueue = _xlapi_dll.xlCanFlushTransmitQueue
xlCanFlushTransmitQueue.argtypes = [xlclass.XLportHandle, xlclass.XLaccess]
xlCanFlushTransmitQueue.restype = xlclass.XLstatus
xlCanFlushTransmitQueue.errcheck = check_status

xlCanSetChannelAcceptance = _xlapi_dll.xlCanSetChannelAcceptance
xlCanSetChannelAcceptance.argtypes = [
    xlclass.XLportHandle,
    xlclass.XLaccess,
    ctypes.c_ulong,
    ctypes.c_ulong,
    ctypes.c_uint,
]
xlCanSetChannelAcceptance.restype = xlclass.XLstatus
xlCanSetChannelAcceptance.errcheck = check_status

xlCanResetAcceptance = _xlapi_dll.xlCanResetAcceptance
xlCanResetAcceptance.argtypes = [xlclass.XLportHandle, xlclass.XLaccess, ctypes.c_uint]
xlCanResetAcceptance.restype = xlclass.XLstatus
xlCanResetAcceptance.errcheck = check_status

xlCanRequestChipState = _xlapi_dll.xlCanRequestChipState
xlCanRequestChipState.argtypes = [xlclass.XLportHandle, xlclass.XLaccess]
xlCanRequestChipState.restype = xlclass.XLstatus
xlCanRequestChipState.errcheck = check_status

xlCanSetChannelOutput = _xlapi_dll.xlCanSetChannelOutput
xlCanSetChannelOutput.argtypes = [xlclass.XLportHandle, xlclass.XLaccess, ctypes.c_char]
xlCanSetChannelOutput.restype = xlclass.XLstatus
xlCanSetChannelOutput.errcheck = check_status

xlPopupHwConfig = _xlapi_dll.xlPopupHwConfig
xlPopupHwConfig.argtypes = [ctypes.c_char_p, ctypes.c_uint]
xlPopupHwConfig.restype = xlclass.XLstatus
xlPopupHwConfig.errcheck = check_status

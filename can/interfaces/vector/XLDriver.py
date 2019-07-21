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

# Vector XL API Definitions
# =========================
from . import XLClass

# Load Windows DLL
DLL_NAME = "vxlapi64" if platform.architecture()[0] == "64bit" else "vxlapi"
_xlapi_dll = ctypes.windll.LoadLibrary(DLL_NAME)


# ctypes wrapping for API functions
xlGetErrorString = _xlapi_dll.xlGetErrorString
xlGetErrorString.argtypes = [XLClass.XLstatus]
xlGetErrorString.restype = ctypes.c_char_p


def check_status(result, function, arguments):
    if result > 0:
        raise VectorError(result, xlGetErrorString(result).decode(), function.__name__)
    return result


xlGetDriverConfig = _xlapi_dll.xlGetDriverConfig
xlGetDriverConfig.argtypes = [ctypes.POINTER(XLClass.XLdriverConfig)]
xlGetDriverConfig.restype = XLClass.XLstatus
xlGetDriverConfig.errcheck = check_status

xlOpenDriver = _xlapi_dll.xlOpenDriver
xlOpenDriver.argtypes = []
xlOpenDriver.restype = XLClass.XLstatus
xlOpenDriver.errcheck = check_status

xlCloseDriver = _xlapi_dll.xlCloseDriver
xlCloseDriver.argtypes = []
xlCloseDriver.restype = XLClass.XLstatus
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
xlGetApplConfig.restype = XLClass.XLstatus
xlGetApplConfig.errcheck = check_status

xlGetChannelIndex = _xlapi_dll.xlGetChannelIndex
xlGetChannelIndex.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelIndex.restype = ctypes.c_int

xlGetChannelMask = _xlapi_dll.xlGetChannelMask
xlGetChannelMask.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelMask.restype = XLClass.XLaccess

xlOpenPort = _xlapi_dll.xlOpenPort
xlOpenPort.argtypes = [
    ctypes.POINTER(XLClass.XLportHandle),
    ctypes.c_char_p,
    XLClass.XLaccess,
    ctypes.POINTER(XLClass.XLaccess),
    ctypes.c_uint,
    ctypes.c_uint,
    ctypes.c_uint,
]
xlOpenPort.restype = XLClass.XLstatus
xlOpenPort.errcheck = check_status

xlGetSyncTime = _xlapi_dll.xlGetSyncTime
xlGetSyncTime.argtypes = [XLClass.XLportHandle, ctypes.POINTER(XLClass.XLuint64)]
xlGetSyncTime.restype = XLClass.XLstatus
xlGetSyncTime.errcheck = check_status

xlClosePort = _xlapi_dll.xlClosePort
xlClosePort.argtypes = [XLClass.XLportHandle]
xlClosePort.restype = XLClass.XLstatus
xlClosePort.errcheck = check_status

xlSetNotification = _xlapi_dll.xlSetNotification
xlSetNotification.argtypes = [
    XLClass.XLportHandle,
    ctypes.POINTER(XLClass.XLhandle),
    ctypes.c_int,
]
xlSetNotification.restype = XLClass.XLstatus
xlSetNotification.errcheck = check_status

xlCanSetChannelMode = _xlapi_dll.xlCanSetChannelMode
xlCanSetChannelMode.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.c_int,
    ctypes.c_int,
]
xlCanSetChannelMode.restype = XLClass.XLstatus
xlCanSetChannelMode.errcheck = check_status

xlActivateChannel = _xlapi_dll.xlActivateChannel
xlActivateChannel.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.c_uint,
    ctypes.c_uint,
]
xlActivateChannel.restype = XLClass.XLstatus
xlActivateChannel.errcheck = check_status

xlDeactivateChannel = _xlapi_dll.xlDeactivateChannel
xlDeactivateChannel.argtypes = [XLClass.XLportHandle, XLClass.XLaccess]
xlDeactivateChannel.restype = XLClass.XLstatus
xlDeactivateChannel.errcheck = check_status

xlCanFdSetConfiguration = _xlapi_dll.xlCanFdSetConfiguration
xlCanFdSetConfiguration.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.POINTER(XLClass.XLcanFdConf),
]
xlCanFdSetConfiguration.restype = XLClass.XLstatus
xlCanFdSetConfiguration.errcheck = check_status

xlReceive = _xlapi_dll.xlReceive
xlReceive.argtypes = [
    XLClass.XLportHandle,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(XLClass.XLevent),
]
xlReceive.restype = XLClass.XLstatus
xlReceive.errcheck = check_status

xlCanReceive = _xlapi_dll.xlCanReceive
xlCanReceive.argtypes = [XLClass.XLportHandle, ctypes.POINTER(XLClass.XLcanRxEvent)]
xlCanReceive.restype = XLClass.XLstatus
xlCanReceive.errcheck = check_status

xlCanSetChannelBitrate = _xlapi_dll.xlCanSetChannelBitrate
xlCanSetChannelBitrate.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.c_ulong,
]
xlCanSetChannelBitrate.restype = XLClass.XLstatus
xlCanSetChannelBitrate.errcheck = check_status

xlCanSetChannelParams = _xlapi_dll.xlCanSetChannelParams
xlCanSetChannelParams.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.POINTER(XLClass.XLchipParams),
]
xlCanSetChannelParams.restype = XLClass.XLstatus
xlCanSetChannelParams.errcheck = check_status

xlCanTransmit = _xlapi_dll.xlCanTransmit
xlCanTransmit.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(XLClass.XLevent),
]
xlCanTransmit.restype = XLClass.XLstatus
xlCanTransmit.errcheck = check_status

xlCanTransmitEx = _xlapi_dll.xlCanTransmitEx
xlCanTransmitEx.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.c_uint,
    ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(XLClass.XLcanTxEvent),
]
xlCanTransmitEx.restype = XLClass.XLstatus
xlCanTransmitEx.errcheck = check_status

xlCanFlushTransmitQueue = _xlapi_dll.xlCanFlushTransmitQueue
xlCanFlushTransmitQueue.argtypes = [XLClass.XLportHandle, XLClass.XLaccess]
xlCanFlushTransmitQueue.restype = XLClass.XLstatus
xlCanFlushTransmitQueue.errcheck = check_status

xlCanSetChannelAcceptance = _xlapi_dll.xlCanSetChannelAcceptance
xlCanSetChannelAcceptance.argtypes = [
    XLClass.XLportHandle,
    XLClass.XLaccess,
    ctypes.c_ulong,
    ctypes.c_ulong,
    ctypes.c_uint,
]
xlCanSetChannelAcceptance.restype = XLClass.XLstatus
xlCanSetChannelAcceptance.errcheck = check_status

xlCanResetAcceptance = _xlapi_dll.xlCanResetAcceptance
xlCanResetAcceptance.argtypes = [XLClass.XLportHandle, XLClass.XLaccess, ctypes.c_uint]
xlCanResetAcceptance.restype = XLClass.XLstatus
xlCanResetAcceptance.errcheck = check_status

xlCanRequestChipState = _xlapi_dll.xlCanRequestChipState
xlCanRequestChipState.argtypes = [XLClass.XLportHandle, XLClass.XLaccess]
xlCanRequestChipState.restype = XLClass.XLstatus
xlCanRequestChipState.errcheck = check_status

xlCanSetChannelOutput = _xlapi_dll.xlCanSetChannelOutput
xlCanSetChannelOutput.argtypes = [XLClass.XLportHandle, XLClass.XLaccess, ctypes.c_char]
xlCanSetChannelOutput.restype = XLClass.XLstatus
xlCanSetChannelOutput.errcheck = check_status

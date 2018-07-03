#!/usr/bin/env python
# coding: utf-8

"""
This wrapper is for windows or direct access via CANAL API.
Socket CAN is recommended under Unix/Linux systems.
"""

import can
from ctypes import *
from struct import *
import logging

log = logging.getLogger('can.usb2can')

# type definitions
flags = c_ulong
pConfigureStr = c_char_p
handle = c_long
timeout = c_ulong
filter = c_ulong

# flags mappings
IS_ERROR_FRAME = 4
IS_REMOTE_FRAME = 2
IS_ID_TYPE = 1


class CanalStatistics(Structure):
    _fields_ = [('ReceiveFrams', c_ulong),
                ('TransmistFrams', c_ulong),
                ('ReceiveData', c_ulong),
                ('TransmitData', c_ulong),
                ('Overruns', c_ulong),
                ('BusWarnings', c_ulong),
                ('BusOff', c_ulong)]


stat = CanalStatistics


class CanalStatus(Structure):
    _fields_ = [('channel_status', c_ulong),
                ('lasterrorcode', c_ulong),
                ('lasterrorsubcode', c_ulong),
                ('lasterrorstr', c_byte * 80)]


# data type for the CAN Message
class CanalMsg(Structure):
    _fields_ = [('flags', c_ulong),
                ('obid', c_ulong),
                ('id', c_ulong),
                ('sizeData', c_ubyte),
                ('data', c_ubyte * 8),
                ('timestamp', c_ulong)]


class Usb2CanAbstractionLayer:
    """A low level wrapper around the usb2can library.

    Documentation: http://www.8devices.com/media/products/usb2can/downloads/CANAL_API.pdf

    """
    def __init__(self):
        self.__m_dllBasic = windll.LoadLibrary("usb2can.dll")

        if self.__m_dllBasic is None:
            log.warning('DLL failed to load')

    def open(self, pConfigureStr, flags):
        try:
            res = self.__m_dllBasic.CanalOpen(pConfigureStr, flags)
            return res
        except:
            log.warning('Failed to open')
            raise

    def close(self, handle):
        try:
            res = self.__m_dllBasic.CanalClose(handle)
            return res
        except:
            log.warning('Failed to close')
            raise

    def send(self, handle, msg):
        try:
            res = self.__m_dllBasic.CanalSend(handle, msg)
            return res
        except:
            log.warning('Sending error')
            raise can.CanError("Failed to transmit frame")

    def receive(self, handle, msg):
        try:
            res = self.__m_dllBasic.CanalReceive(handle, msg)
            return res
        except:
            log.warning('Receive error')
            raise

    def blocking_send(self, handle, msg, timeout):
        try:
            res = self.__m_dllBasic.CanalBlockingSend(handle, msg, timeout)
            return res
        except:
            log.warning('Blocking send error')
            raise

    def blocking_receive(self, handle, msg, timeout):
        try:
            res = self.__m_dllBasic.CanalBlockingReceive(handle, msg, timeout)
            return res
        except:
            log.warning('Blocking Receive Failed')
            raise

    def get_status(self, handle, CanalStatus):
        try:
            res = self.__m_dllBasic.CanalGetStatus(handle, CanalStatus)
            return res
        except:
            log.warning('Get status failed')
            raise

    def get_statistics(self, handle, CanalStatistics):
        try:
            res = self.__m_dllBasic.CanalGetStatistics(handle, CanalStatistics)
            return res
        except:
            log.warning('Get Statistics failed')
            raise

    def get_version(self):
        try:
            res = self.__m_dllBasic.CanalGetVersion()
            return res
        except:
            log.warning('Failed to get version info')
            raise

    def get_library_version(self):
        try:
            res = self.__m_dllBasic.CanalGetDllVersion()
            return res
        except:
            log.warning('Failed to get DLL version')
            raise

    def get_vendor_string(self):
        try:
            res = self.__m_dllBasic.CanalGetVendorString()
            return res
        except:
            log.warning('Failed to get vendor string')
            raise

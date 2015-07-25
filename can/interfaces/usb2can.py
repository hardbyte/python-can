# This wrapper is for windows or direct access via CANAL API.  Socket CAN is recommended under Unix/Linux systems

from ctypes import *
from struct import *
import logging
# import collections
logging.basicConfig(filename='can2usb.log', level=logging.DEBUG)
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


msg = CanalMsg


class usb2can:
    def __init__(self):
        self.__m_dllBasic = windll.LoadLibrary("usb2can.dll")

        if self.__m_dllBasic == None:
            logging.warning('DLL failed to load')

    def CanalOpen(self, pConfigureStr, flags):
        try:
            res = self.__m_dllBasic.CanalOpen(pConfigureStr, flags)
            return res
        except:
            logging.warning('Failed to open')
            raise

    def CanalClose(self, handle):
        try:
            res = self.__m_dllBasic.CanalClose(handle)
            return res
        except:
            logging.warning('Failed to close')
            raise

    def CanalSend(self, handle, msg):
        try:
            res = self.__m_dllBasic.CanalSend(handle, msg)
            return res
        except:
            logging.warning('Sending error')
            raise

    def CanalReceive(self, handle, msg):
        try:
            res = self.__m_dllBasic.CanalReceive(handle, msg)
            return res
        except:
            logging.warning('Receive error')
            raise

    def CanalBlockingSend(self, handle, msg, timeout):
        try:
            res = self.__m_dllBasic.CanalBlockingSend(handle, msg, timeout)
            return res
        except:
            logging.warning('Blocking send error')
            raise

    def CanalBlockingReceive(self, handle, msg, timeout):
        try:
            res = self.__m_dllBasic.CanalBlockingReceive(handle, msg, timeout)
            return res
        except:
            logging.warning('Blocking Receive Failed')
            raise

    def CanalGetStatus(self, handle, CanalStatus):
        try:
            res = self.__m_dllBasic.CanalGetStatus(handle, CanalStatus)
            return res
        except:
            logging.warning('Get status failed')
            raise

    def CanalGetStatistics(self, handle, CanalStatistics):
        try:
            res = self.__m_dllBasic.CanalGetStatistics(handle, CanalStatistics)
            return res
        except:
            logging.warning('Get Statistics failed')
            raise

    def CanalGetVersion(self):
        try:
            res = self.__m_dllBasic.CanalGetVersion()
            return res
        except:
            logging.warning('Failed to get version info')
            raise

    def CanalGetDllVersion(self):
        try:
            res = self.__m_dllBasic.CanalGetDllVersion()
            return res
        except:
            logging.warning('Failed to get DLL version')
            raise

    def CanalGetVendorString(self):
        try:
            res = self.__m_dllBasic.CanalGetVendorString()
            return res
        except:
            logging.warning('Failed to get vendor string')
            raise

import atexit
import ctypes
import logging
import Queue
import time
import types

import canlib
import canstat

canlib.canInitializeLibrary()
canModuleLogger = logging.getLogger("pycanlib.CAN")

class pycanlibError(Exception):
    pass


TIMER_TICKS_PER_SECOND = 1000


class InvalidParameterError(pycanlibError):

    def __init__(self, parameterName, parameterValue, reason):
        self.parameterName = parameterName
        self.parameterValue = parameterValue
        self.reason = reason

    def __str__(self):
        return ("%s: invalid value '%s' for parameter '%s' - %s" %
          (self.__class__.__name__, self.parameterValue,
          self.parameterName, self.reason))


class InvalidMessageParameterError(InvalidParameterError):
    pass


class InvalidBusParameterError(InvalidParameterError):
    pass


class LogMessage(object):

    def __init__(self, timestamp=0.0):
        canModuleLogger.debug("Starting LogMessage.__init__ - timestamp %s"
          % timestamp)
        if not isinstance(timestamp, types.FloatType):
            badTimestampError = InvalidMessageParameterError("timestamp",
              timestamp, ("expected float; received '%s'" %
              timestamp.__class__.__name__))
            canModuleLogger.debug("LogMessage.__init__: %s" %
              badTimestampError)
            raise badTimestampError
        if timestamp >= 0:
            self.timestamp = timestamp
        else:
            badTimestampError = InvalidMessageParameterError("timestamp",
              timestamp, "timestamp value must be positive")
            canModuleLogger.debug("LogMessage.__init__: %s" %
              badTimestampError)
            raise badTimestampError
        canModuleLogger.debug("LogMessage.__init__ completed successfully")

    def __str__(self):
        return "%.6f" % self.timestamp


class Message(LogMessage):

    def __init__(self, deviceID=0, data=[], dlc=0, flags=0, timestamp=0.0):
        LogMessage.__init__(self, timestamp)
        if not isinstance(deviceID, types.IntType):
            raise InvalidMessageParameterError("deviceID", deviceID,
              ("expected int; received '%s'" %
              deviceID.__class__.__name__))
        if deviceID not in range(0, 2 ** 11):
            raise InvalidMessageParameterError("deviceID", deviceID,
              "deviceID must be in range [0, 2**11-1]")
        self.deviceID = deviceID
        if len(data) not in range(0, 9):
            raise InvalidMessageParameterError("data", data,
              "data array length must be in range [0, 8]")
        for item in data:
            if not isinstance(item, types.IntType):
                raise InvalidMessageParameterError("data", data,
                  ("data array must contain only integers; found '%s'" %
                  item.__class__.__name__))
            if item not in range(0, 2 ** 8):
                raise InvalidMessageParameterError("data", data,
                  "data array element values must be in range [0, 2**8-1]")
        self.data = data
        if not isinstance(dlc, types.IntType):
            raise InvalidMessageParameterError("dlc", dlc,
              "expected int; received %s" % dlc.__class__.__name__)
        if dlc not in range(0, 9):
            raise InvalidMessageParameterError("dlc", dlc,
              "DLC value must be in range [0, 8]")
        self.dlc = dlc
        if not isinstance(flags, types.IntType):
            raise InvalidMessageParameterError("flags", flags,
              "expected int; received %s" % flags.__class__.__name__)
        if flags not in range(0, 2 ** 16):
            raise InvalidMessageParameterError("flags", flags,
              "flags value must be in range [0, 2**16-1]")
        self.flags = flags

    def __str__(self):
        _fieldStrings = []
        _fieldStrings.append(LogMessage.__str__(self))
        _fieldStrings.append("%.4x" % self.deviceID)
        _fieldStrings.append("%.4x" % self.flags)
        _fieldStrings.append("%d" % self.dlc)
        _dataStrings = []
        for byte in self.data:
            _dataStrings.append("%.2x" % byte)
        if len(_dataStrings) > 0:
            _fieldStrings.append(" ".join(_dataStrings))
        return "\t".join(_fieldStrings)


class InfoMessage(LogMessage):

    def __init__(self, timestamp=0.0, info=None):
        LogMessage.__init__(self, timestamp)
        self.info = info

    def __str__(self):
        if self.info != None:
            return ("%s\t%s" % (LogMessage.__str__(self), self.info))
        else:
            return "%s" % LogMessage.__str__(self)


readHandleRegistry = {}
writeHandleRegistry = {}


def _ReceiveCallback(handle):
    readHandleRegistry[handle].ReceiveCallback()
    return 0


RX_CALLBACK = canlib.CALLBACKFUNC(_ReceiveCallback)


def _TransmitCallback(handle):
    writeHandleRegistry[handle].TransmitCallback()
    return 0


TX_CALLBACK = canlib.CALLBACKFUNC(_TransmitCallback)


class _Handle(object):

    def __init__(self, channel, flags):
        _numChannels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
        if channel not in range(0, _numChannels.value):
            raise InvalidBusParameterError("channel", channel,
              ("available channels on this system are in the range [0, %d]" %
              _numChannels.value))
        if flags & (0xFFFF - canlib.FLAGS_MASK) != 0:
            raise InvalidBusParameterError("flags", flags,
              "must contain only the canOPEN_* flags listed in canlib.py")
        self.flags = flags
        try:
            self.canlibHandle = canlib.canOpenChannel(channel, flags)
        except CANLIBErrorHandlers.CANLIBError as e:
            if e.errorCode == canstat.canERR_NOTFOUND:
                raise InvalidBusParameterError("flags", flags,
                  "no hardware is available that has all these capabilities")
            else:
                raise
        self.listeners = []#real-time response - for emulated devices, etc.
        self.buses = []#non-real-time response - for test cases, etc.
        self.txQueue = Queue.Queue(0)
        canlib.canBusOn(self.canlibHandle)

    def TransmitCallback(self):
        print "Transmit callback for handle %d" % self.canlibHandle

    def ReceiveCallback(self):
        deviceID = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_long(0)
        canlib.canRead(self.canlibHandle, ctypes.byref(deviceID),
          ctypes.byref(data), ctypes.byref(dlc), ctypes.byref(flags),
          ctypes.byref(timestamp))
        _data = []
        for char in data:
            _data.append(ord(char))
        rxMsg = Message(deviceID.value, _data[:dlc.value], int(dlc.value),
          int(flags.value), float(timestamp.value)/TIMER_TICKS_PER_SECOND)
        for _bus in self.buses:
            _bus.rxQueue.put_nowait(rxMsg)
        for _listener in self.listeners:
            _listener.OnMessageReceived(rxMsg)

def _GetHandle(channelNumber, flags, registry):
    foundHandle = False
    handle = None
    for _key in registry.keys():
        if (_key == channelNumber) and (registry[_key].flags == flags):
            foundHandle = True
            handle = registry[_key].canlibHandle
    if not foundHandle:
        newHandle = _Handle(channelNumber, flags)
        registry[newHandle.canlibHandle] = newHandle
        handle = newHandle.canlibHandle
    if registry == readHandleRegistry:
        canlib.kvSetNotifyCallback(registry[handle].canlibHandle, RX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_RX)
    else:
        canlib.kvSetNotifyCallback(registry[handle].canlibHandle, TX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_TX)
    return registry[handle]


@atexit.register
def Cleanup():
    for handle in readHandleRegistry.keys():
        canlib.kvSetNotifyCallback(handle, None, None, canstat.canNOTIFY_RX)
    for handle in writeHandleRegistry.keys():
        canlib.kvSetNotifyCallback(handle, None, None, canstat.canNOTIFY_TX)
    time.sleep(0.001)

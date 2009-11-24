import atexit
import ctypes
import logging
import Queue
import time
import types

import canlib
import CANLIBErrorHandlers
import canstat

canlib.canInitializeLibrary()
canModuleLogger = logging.getLogger("pycanlib.CAN")


class pycanlibError(Exception):
    pass


TIMER_TICKS_PER_SECOND = 1000000
MICROSECONDS_PER_TIMER_TICK = TIMER_TICKS_PER_SECOND/1000000


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
    canModuleLogger.debug("_ReceiveCallback for handle %d" % handle)
    readHandleRegistry[handle].ReceiveCallback()
    return 0


RX_CALLBACK = canlib.CALLBACKFUNC(_ReceiveCallback)


def _TransmitCallback(handle):
    canModuleLogger.debug("_TransmitCallback for handle %d" % handle)
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
        self.channel = channel
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
        _tmrRes = ctypes.c_long(MICROSECONDS_PER_TIMER_TICK)
        canlib.canIoCtl(self.canlibHandle, canlib.canIOCTL_SET_TIMER_SCALE,
          ctypes.byref(_tmrRes), 4)
        canlib.canBusOn(self.canlibHandle)

    def TransmitCallback(self):
        try:
            toSend = self.txQueue.get_nowait()
        except Queue.Empty:
            return
        _dataString = "".join([("%c" % byte) for byte in toSend.data])
        canlib.canWrite(self.canlibHandle, toSend.deviceID, _dataString,
          toSend.dlc, toSend.flags)

    def ReceiveCallback(self):
        canlib.kvSetNotifyCallback(self.canlibHandle, None, None,
          canstat.canNOTIFY_RX)
        deviceID = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_long(0)
        canModuleLogger.info("entering ReceiveCallback while loop")
        while True:
            try:
                canlib.canRead(self.canlibHandle, ctypes.byref(deviceID),
                  ctypes.byref(data), ctypes.byref(dlc), ctypes.byref(flags),
                  ctypes.byref(timestamp))
            except CANLIBErrorHandlers.CANLIBError as e:
                if e.errorCode == canstat.canERR_NOMSG:
                    canModuleLogger.info("exiting ReceiveCallback while loop")
                    break
                else:
                    raise
            _data = []
#            rxMsg = (deviceID.value, data, dlc.value, flags.value, float(timestamp.value)/TIMER_TICKS_PER_SECOND)
            for char in data:
                _data.append(ord(char))
            rxMsg = Message(deviceID.value, _data[:dlc.value], int(dlc.value),
              int(flags.value), float(timestamp.value) / TIMER_TICKS_PER_SECOND)
            for _bus in self.buses:
                _bus.rxQueue.put_nowait(rxMsg)
            for _listener in self.listeners:
                _listener.OnMessageReceived(rxMsg)
        canlib.kvSetNotifyCallback(self.canlibHandle, RX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_RX)

    def ReadTimer(self):
        return canlib.canReadTimer(self.canlibHandle)


def _GetHandle(channelNumber, flags, registry):
    foundHandle = False
    handle = None
    for _key in registry.keys():
        if (registry[_key].channel == channelNumber) and \
          (registry[_key].flags == flags):
            foundHandle = True
            handle = registry[_key]
    if not foundHandle:
        handle = _Handle(channelNumber, flags)
        registry[handle.canlibHandle] = handle
    if registry == readHandleRegistry:
        canModuleLogger.info("Setting notify callback for read handle %d" %
          handle.canlibHandle)
        canlib.kvSetNotifyCallback(handle.canlibHandle, RX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_RX)
    else:
        canModuleLogger.info("Setting notify callback for write handle %d" %
          handle.canlibHandle)
        canlib.kvSetNotifyCallback(handle.canlibHandle, TX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_TX)
    return handle


#def _CalculateSegmentLengths(busSpeed, clockFreq):
#    retVal = []
#    for prescaler in range(1, 65):#Kvaser Leaf has an 82C250 type transceiver, which has a prescaler of 64
#        btq = clockFreq / busSpeed / 2 / prescaler
#        if btq >= 4 and btq <= 32:
#            err = (btq * prescaler) / (btq - 1)
#            for t1 in range(3, 18):
#                t2 = btq - t1
#                if (t1 > t2) and (t2 < 8) and (t2 > 2):
#                    canModuleLogger.info("clockFreq = %d, busSpeed = %d, tseg1 = %d, tseg2 = %d" % (clockFreq, busSpeed, t1, t2))
#                    retVal.append((t1, t2))
#    return retVal

#CLOCK_FREQ = 16000000

class Bus(object):

    def __init__(self, channel=0, flags=0, speed=1000000, tseg1=1, tseg2=0,
                 sjw=1, noSamp=1):
        canModuleLogger.info("Getting read handle for new Bus instance")
        self.readHandle = _GetHandle(channel, flags, readHandleRegistry)
        canModuleLogger.info("Read handle is %d" %
                             self.readHandle.canlibHandle)
        canModuleLogger.info("Getting write handle for new Bus instance")
        self.writeHandle = _GetHandle(channel, flags, writeHandleRegistry)
        canModuleLogger.info("Write handle is %s" %
                             self.writeHandle.canlibHandle)
#        _segLengths = _CalculateSegmentLengths(speed, CLOCK_FREQ)
#        _tseg1Vals = []
#        _tseg2Vals = []
#        for _segLengthPair in _segLengths:
#            _tseg1Vals.append(_segLengthPair[0])
#            _tseg2Vals.append(_segLengthPair[1])
#        if tseg1 not in _tseg1Vals:
#            raise InvalidBusParameterError("tseg1", tseg1,
#              "value must be in set %s" % _tseg1Vals)
#        if tseg2 not in _tseg2Vals:
#            raise InvalidBusParameterError("tseg2", tseg2,
#              "value must be in set %s" % _tseg2Vals)
        _oldSpeed = ctypes.c_long(0)
        _oldTseg1 = ctypes.c_uint(0)
        _oldTseg2 = ctypes.c_uint(0)
        _oldSJW = ctypes.c_uint(0)
        _oldSampleNo = ctypes.c_uint(0)
        _oldSyncMode = ctypes.c_uint(0)
        canlib.canGetBusParams(self.readHandle.canlibHandle,
          ctypes.byref(_oldSpeed), ctypes.byref(_oldTseg1),
          ctypes.byref(_oldTseg2), ctypes.byref(_oldSJW),
          ctypes.byref(_oldSampleNo), ctypes.byref(_oldSyncMode))
        if ((speed != _oldSpeed.value) or (tseg1 != _oldTseg1.value) or
            (tseg2 != _oldTseg2.value) or (sjw != _oldSJW.value) or
            (noSamp != _oldSampleNo.value)):
            canlib.canBusOff(self.readHandle.canlibHandle)
            canlib.canSetBusParams(self.readHandle.canlibHandle, speed, tseg1,
                                   tseg2, sjw, noSamp, 0)
            canlib.canBusOn(self.readHandle.canlibHandle)
        canlib.canGetBusParams(self.writeHandle.canlibHandle,
          ctypes.byref(_oldSpeed), ctypes.byref(_oldTseg1),
          ctypes.byref(_oldTseg2), ctypes.byref(_oldSJW),
          ctypes.byref(_oldSampleNo), ctypes.byref(_oldSyncMode))
        if ((speed != _oldSpeed.value) or (tseg1 != _oldTseg1.value) or
            (tseg2 != _oldTseg2.value) or (sjw != _oldSJW.value) or
            (noSamp != _oldSampleNo.value)):
            canlib.canBusOff(self.writeHandle.canlibHandle)
            canlib.canSetBusParams(self.writeHandle.canlibHandle, speed, tseg1,
                                   tseg2, sjw, noSamp, 0)
            canlib.canBusOn(self.writeHandle.canlibHandle)
        self.rxQueue = Queue.Queue(0)
        self.timerOffset = self.readHandle.ReadTimer()
        self.readHandle.buses.append(self)

    def Read(self):
        try:
            return self.rxQueue.get_nowait()
        except Queue.Empty:
            canModuleLogger.debug("No messages available")
            return None

    def Write(self, msg):
        self.writeHandle.txQueue.put_nowait(msg)
        _TransmitCallback(self.writeHandle.canlibHandle)

    def ReadTimer(self):
        return (float(self.readHandle.ReadTimer() - self.timerOffset) /
          TIMER_TICKS_PER_SECOND)


@atexit.register
def Cleanup():
    for handle in readHandleRegistry.keys():
        canlib.kvSetNotifyCallback(handle, None, None, canstat.canNOTIFY_RX)
    for handle in writeHandleRegistry.keys():
        canlib.kvSetNotifyCallback(handle, None, None, canstat.canNOTIFY_TX)
    time.sleep(0.001)

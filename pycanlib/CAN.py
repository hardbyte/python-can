import atexit
import ctypes
import logging
import os
import Queue
import sys
import time
import types
from xml.dom import minidom

import canlib
import CANLIBErrorHandlers
import canstat

canlib.canInitializeLibrary()


canModuleLogger = logging.getLogger("pycanlib.CAN")
handleClassLogger = logging.getLogger("pycanlib.CAN._Handle")
busClassLogger = logging.getLogger("pycanlib.CAN.Bus")
logMessageClassLogger = logging.getLogger("pycanlib.CAN.LogMessage")
messageClassLogger = logging.getLogger("pycanlib.CAN.Message")
infoMessageClassLogger = logging.getLogger("pycanlib.CAN.InfoMessage")


try:
    _versionNumberFile = open(os.path.join(os.path.dirname(__file__),
                              "version.txt"), "r")
    __version__ = _versionNumberFile.readline()
    _versionNumberFile.close()
except IOError as e:#pragma: no cover
    print e
    __version__ = "UNKNOWN"


class pycanlibError(Exception):
    pass


TIMER_TICKS_PER_SECOND = 1000000
MICROSECONDS_PER_TIMER_TICK = (TIMER_TICKS_PER_SECOND / 1000000)


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
        _startMsg = "Starting LogMessage.__init__ - timestamp %s" % timestamp
        logMessageClassLogger.debug(_startMsg)
        if not isinstance(timestamp, types.FloatType):
            badTimestampError = InvalidMessageParameterError("timestamp",
              timestamp, ("expected float; received '%s'" %
              timestamp.__class__.__name__))
            logMessageClassLogger.debug("LogMessage.__init__: %s" %
              badTimestampError)
            raise badTimestampError
        if timestamp < 0:
            badTimestampError = InvalidMessageParameterError("timestamp",
              timestamp, "timestamp value must be positive")
            logMessageClassLogger.debug("LogMessage.__init__: %s" %
              badTimestampError)
            raise badTimestampError
        self.timestamp = timestamp
        _finishMsg = "LogMessage.__init__ completed successfully"
        logMessageClassLogger.debug(_finishMsg)

    def __str__(self):
        return "%.6f" % self.timestamp

    def ToXML(self, elementType="log_message"):
        _document = minidom.Document()
        retVal = _document.createElement(elementType)
        timestampElement = _document.createElement("timestamp")
        timestampTextNode = _document.createTextNode("%s" % self.timestamp)
        timestampElement.appendChild(timestampTextNode)
        retVal.appendChild(timestampElement)
        return retVal


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

    def ToXML(self):
        _document = minidom.Document()
        retVal = LogMessage.ToXML(self, "can_message")
        deviceIDElement = _document.createElement("device_id")
        deviceIDTextNode = _document.createTextNode("%.4x" % self.deviceID)
        deviceIDElement.appendChild(deviceIDTextNode)
        flagsElement = _document.createElement("flags")
        flagsTextNode = _document.createTextNode("%.4x" % self.flags)
        flagsElement.appendChild(flagsTextNode)
        dlcElement = _document.createElement("dlc")
        dlcTextNode = _document.createTextNode("%d" % self.dlc)
        dlcElement.appendChild(dlcTextNode)
        retVal.appendChild(deviceIDElement)
        retVal.appendChild(flagsElement)
        retVal.appendChild(dlcElement)
        if len(self.data) > 0:
            dataElement = _document.createElement("data")
            for i in xrange(len(self.data)):
                dataByteElement = _document.createElement("byte_%d" % i)
                dataByteTextNode = \
                  _document.createTextNode("%.2x" % self.data[i])
                dataByteElement.appendChild(dataByteTextNode)
                dataElement.appendChild(dataByteElement)
            retVal.appendChild(dataElement)
        return retVal

class InfoMessage(LogMessage):

    def __init__(self, timestamp=0.0, info=None):
        LogMessage.__init__(self, timestamp)
        self.info = info

    def __str__(self):
        if self.info != None:
            return ("%s\t%s" % (LogMessage.__str__(self), self.info))
        else:
            return "%s" % LogMessage.__str__(self)

    def ToXML(self):
        _document = minidom.Document()
        retVal = LogMessage.ToXML(self, "info_message")
        _infoStringElement = _document.createElement("info_string")
        _infoStringTextNode = _document.createTextNode(self.info)
        _infoStringElement.appendChild(_infoStringTextNode)
        retVal.appendChild(_infoStringElement)
        return retVal


readHandleRegistry = {}
writeHandleRegistry = {}


def _ReceiveCallback(handle):#pragma: no cover
    #called by the callback registered with CANLIB, but coverage can't figure
    #that out
    canModuleLogger.debug("Entering _ReceiveCallback for handle %d" % handle)
    if readHandleRegistry[handle] != None:
        readHandleRegistry[handle].ReceiveCallback()
    canModuleLogger.debug("Leaving _ReceiveCallback for handle %d" % handle)
    return 0


RX_CALLBACK = canlib.CALLBACKFUNC(_ReceiveCallback)


def _TransmitCallback(handle):
    canModuleLogger.debug("Entering _TransmitCallback for handle %d" %
                            handle)
    if writeHandleRegistry[handle] != None:
        writeHandleRegistry[handle].TransmitCallback()
    canModuleLogger.debug("Leaving _TransmitCallback for handle %d" % handle)
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
            else:#pragma: no cover
                raise
        self.listeners = []
        self.txQueue = Queue.Queue(0)
        _tmrRes = ctypes.c_long(MICROSECONDS_PER_TIMER_TICK)
        canlib.canFlushReceiveQueue(self.canlibHandle)
        canlib.canFlushTransmitQueue(self.canlibHandle)
        canlib.canIoCtl(self.canlibHandle, canlib.canIOCTL_SET_TIMER_SCALE,
          ctypes.byref(_tmrRes), 4)
        canlib.canBusOn(self.canlibHandle)
        self.reading = False
        self.writing = False
        self.receiveCallbackEnabled = True
        self.transmitCallbackEnabled = True

    def TransmitCallback(self):
        handleClassLogger.debug("Transmit buffer level for handle %d: %d" %
          (self.canlibHandle, self.GetTransmitBufferLevel()))
        if not self.writing and self.transmitCallbackEnabled:
            self.writing = True
            try:
                toSend = self.txQueue.get_nowait()
            except Queue.Empty:#pragma: no cover
                #this part of TransmitCallback executes when CANLIB fires the
                #transmit callback event for this handle, but coverage isn't
                #smart enough to figure this out, so it thinks it isn't called
                #at all
                self.writing = False
                return
            _dataString = "".join([("%c" % byte) for byte in toSend.data])
            canlib.canWrite(self.canlibHandle, toSend.deviceID, _dataString,
              toSend.dlc, toSend.flags)
            self.writing = False

    def Write(self, msg):
        oldSize = self.txQueue.qsize()
        self.txQueue.put_nowait(msg)
        if oldSize == 0:
            self.TransmitCallback()

    def ReceiveCallback(self):#pragma: no cover
        #this is called by the callback registered with CANLIB, but because
        #coverage isn't smart enough to figure this out, it thinks this
        #function is never called at all
        _callbackEntryMsg = "Entering _Handle.ReceiveCallback"
        handleClassLogger.info(_callbackEntryMsg)
        if not self.reading and self.receiveCallbackEnabled:
            self.reading = True
            deviceID = ctypes.c_long(0)
            data = ctypes.create_string_buffer(8)
            dlc = ctypes.c_uint(0)
            flags = ctypes.c_uint(0)
            flags = ctypes.c_uint(0)
            timestamp = ctypes.c_long(0)
            status = canstat.c_canStatus(canstat.canOK)
            status = canlib.canRead(self.canlibHandle,
              ctypes.byref(deviceID), ctypes.byref(data),
              ctypes.byref(dlc), ctypes.byref(flags),
              ctypes.byref(timestamp))
            while status.value == canstat.canOK:
                _data = []
                for char in data:
                    _data.append(ord(char))
                handleClassLogger.debug("Creating new Message object")
                rxMsg = Message(deviceID.value, _data[:dlc.value],
                  int(dlc.value), int(flags.value), (float(timestamp.value) /
                  TIMER_TICKS_PER_SECOND))
                for _listener in self.listeners:
                    _listener.OnMessageReceived(rxMsg)
                status = canlib.canRead(self.canlibHandle,
                  ctypes.byref(deviceID), ctypes.byref(data),
                  ctypes.byref(dlc), ctypes.byref(flags),
                  ctypes.byref(timestamp))
            _exitStr = "Leaving _Handle.ReceiveCallback - status is %s (%d)"
            _callbackExitMessage = (_exitStr %
              (canstat.canStatusLookupTable[status.value], status.value))
            handleClassLogger.info(_callbackExitMessage)
            canlib.kvSetNotifyCallback(self.canlibHandle, RX_CALLBACK,
              ctypes.c_void_p(None), canstat.canNOTIFY_RX)
            self.reading = False

    def AddListener(self, listener):
        self.listeners.append(listener)

    def ReadTimer(self):
        return canlib.canReadTimer(self.canlibHandle)

    def GetReceiveBufferLevel(self):#pragma: no cover
        #this is called by the callback registered with CANLIB, but because
        #coverage isn't smart enough to figure this out, it thinks this
        #function is never called at all
        rxLevel = ctypes.c_int(0)
        canlib.canIoCtl(self.canlibHandle,
          canlib.canIOCTL_GET_RX_BUFFER_LEVEL, ctypes.byref(rxLevel), 4)
        return rxLevel.value

    def GetTransmitBufferLevel(self):
        txLevel = ctypes.c_int(0)
        canlib.canIoCtl(self.canlibHandle,
          canlib.canIOCTL_GET_TX_BUFFER_LEVEL, ctypes.byref(txLevel), 4)
        return txLevel.value

    def GetDeviceDescription(self):#pragma: no cover
        MAX_DEVICE_DESCR_LENGTH = 256
        _buffer = ctypes.create_string_buffer(MAX_DEVICE_DESCR_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_DEVDESCR_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_DEVICE_DESCR_LENGTH))
        return _buffer.value

    def GetDeviceManufacturerName(self):#pragma: no cover
        MAX_MANUFACTURER_NAME_LENGTH = 256
        _buffer = ctypes.create_string_buffer(MAX_MANUFACTURER_NAME_LENGTH)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_MFGNAME_ASCII, ctypes.byref(_buffer),
          ctypes.c_size_t(MAX_MANUFACTURER_NAME_LENGTH))
        return _buffer.value

    def GetDeviceFirmwareVersion(self):#pragma: no cover
        LENGTH = 8
        UCHAR_ARRAY = ctypes.c_ubyte * LENGTH
        _buffer = UCHAR_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_FIRMWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(LENGTH))
        versionNumber = []
        for i in [6, 4, 0, 2]:
            versionNumber.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d.%d.%d" % (versionNumber[0], versionNumber[1],
          versionNumber[2], versionNumber[3])

    def GetDeviceHardwareVersion(self):#pragma: no cover
        LENGTH = 8
        UCHAR_ARRAY = ctypes.c_ubyte * LENGTH
        _buffer = UCHAR_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_HARDWARE_REV, ctypes.byref(_buffer),
          ctypes.c_size_t(LENGTH))
        versionNumber = []
        for i in [2, 0]:
            versionNumber.append((_buffer[i + 1] << 8) + _buffer[i])
        return "%d.%d" % (versionNumber[0], versionNumber[1])

    def GetDeviceCardSerial(self):#pragma: no cover
        LENGTH = 8
        UCHAR_ARRAY = ctypes.c_ubyte * LENGTH
        _buffer = UCHAR_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(LENGTH))
        _serialNo = 0
        for i in xrange(len(_buffer)):
            _serialNo += (_buffer[i] << (8 * i))
        return _serialNo

    def GetDeviceTransceiverSerial(self):#pragma: no cover
        LENGTH = 8
        UCHAR_ARRAY = ctypes.c_ubyte * LENGTH
        _buffer = UCHAR_ARRAY()
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_SERIAL_NO, ctypes.byref(_buffer),
          ctypes.c_size_t(LENGTH))
        _serialNo = 0
        for i in xrange(len(_buffer)):
            _serialNo += (_buffer[i] << (8 * i))
        return _serialNo

    def GetDeviceCardNumber(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CARD_NUMBER, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    def GetDeviceChannelOnCard(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_CHAN_NO_ON_CARD, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        return _buffer.value

    def GetDeviceTransceiverType(self):#pragma: no cover
        _buffer = ctypes.c_ulong(0)
        canlib.canGetChannelData(self.channel,
          canlib.canCHANNELDATA_TRANS_TYPE, ctypes.byref(_buffer),
          ctypes.c_size_t(4))
        try:
            return canstat.canTransceiverTypeStrings[_buffer.value]
        except KeyError:
            return "Transceiver type %d is unknown to CANLIB" % _buffer.value

    def GetStatistics(self):
        canlib.canRequestBusStatistics(self.canlibHandle)
        _statStruct = canlib.c_canBusStatistics()
        canlib.canGetBusStatistics(self.canlibHandle,
          ctypes.byref(_statStruct), ctypes.c_uint(28))
        return BusStatistics(_statStruct.stdData,
                             _statStruct.stdRemote,
                             _statStruct.extData,
                             _statStruct.extRemote,
                             _statStruct.errFrame,
                             _statStruct.busLoad,
                             _statStruct.overruns)

class BusStatistics(object):
    def __init__(self, stdData, stdRemote, extData, extRemote, errFrame,
      busLoad, overruns):
        self.stdData = stdData
        self.stdRemote = stdRemote
        self.extData = extData
        self.extRemote = extRemote
        self.errFrame = errFrame
        self.busLoad = float(busLoad)/100
        self.overruns = overruns


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
        canModuleLogger.debug("Setting notify callback for read handle %d" %
          handle.canlibHandle)
        canlib.kvSetNotifyCallback(handle.canlibHandle, RX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_RX)
    else:
        canModuleLogger.debug("Setting notify callback for write handle %d" %
          handle.canlibHandle)
        canlib.kvSetNotifyCallback(handle.canlibHandle, TX_CALLBACK,
          ctypes.c_void_p(None), canstat.canNOTIFY_TX)
    return handle


class ChannelInfo(object):#pragma: no cover

    def __init__(self, channel, name, manufacturer, fwVersion, hwVersion,
      cardSN, transSN, transType, cardNo, channelOnCard):
        self.channel = channel
        self.name = name
        self.manufacturer = manufacturer
        self.fwVersion = fwVersion
        self.hwVersion = hwVersion
        self.cardSN = cardSN
        self.transSN = transSN
        self.transType = transType
        self.cardNo = cardNo
        self.channelOnCard = channelOnCard

    def __str__(self):
        retVal = "CANLIB channel: %s\n" % self.channel
        retVal += "Name: %s\n" % self.name
        retVal += "Manufacturer: %s\n" % self.manufacturer
        retVal += "Firmware version: %s\n" % self.fwVersion
        retVal += "Hardware version: %s\n" % self.hwVersion
        retVal += "Card serial number: %s\n" % self.cardSN
        retVal += "Transceiver type: %s\n" % self.transType
        retVal += "Transceiver serial number: %s\n" % self.transSN
        retVal += "Card number: %s\n" % self.cardNo
        retVal += "Channel on card: %s\n" % self.channelOnCard
        return retVal

    def ToXML(self):
        _document = minidom.Document()
        retVal = _document.createElement("channel_info")
        _channelNumberElement = _document.createElement("canlib_channel")
        _channelNumberText = _document.createTextNode("%d" % self.channel)
        _channelNumberElement.appendChild(_channelNumberText)
        retVal.appendChild(_channelNumberElement)
        _channelNameElement = _document.createElement("device_name")
        _channelNameText = _document.createTextNode(self.name)
        _channelNameElement.appendChild(_channelNameText)
        retVal.appendChild(_channelNameElement)
        _channelManufacturerElement = _document.createElement("device_manufacturer")
        _channelManufacturerText = _document.createTextNode(self.manufacturer)
        _channelManufacturerElement.appendChild(_channelManufacturerText)
        retVal.appendChild(_channelManufacturerElement)
        _channelFWVersionElement = _document.createElement("device_firmware_version")
        _channelFWVersionText = _document.createTextNode(self.fwVersion)
        _channelFWVersionElement.appendChild(_channelFWVersionText)
        retVal.appendChild(_channelFWVersionElement)
        _channelHWVersionElement = _document.createElement("device_hardware_version")
        _channelHWVersionText = _document.createTextNode(self.hwVersion)
        _channelHWVersionElement.appendChild(_channelHWVersionText)
        retVal.appendChild(_channelHWVersionElement)
        _channelCardSNElement = _document.createElement("device_serial_number")
        _channelCardSNText = _document.createTextNode("%s" % self.cardSN)
        _channelCardSNElement.appendChild(_channelCardSNText)
        retVal.appendChild(_channelCardSNElement)
        _channelTransceiverTypeElement = _document.createElement("transceiver_type")
        _channelTransceiverTypeText = _document.createTextNode(self.transType)
        _channelTransceiverTypeElement.appendChild(_channelTransceiverTypeText)
        retVal.appendChild(_channelTransceiverTypeElement)
        _channelTransceiverSNElement = _document.createElement("transceiver_serial_number")
        _channelTransceiverSNText = _document.createTextNode("%s" % self.transSN)
        _channelTransceiverSNElement.appendChild(_channelTransceiverSNText)
        retVal.appendChild(_channelTransceiverSNElement)
        _channelCardNumberElement = _document.createElement("card_number")
        _channelCardNumberText = _document.createTextNode("%s" % self.cardNo)
        _channelCardNumberElement.appendChild(_channelCardNumberText)
        retVal.appendChild(_channelCardNumberElement)
        _channelChannelOnCardElement = _document.createElement("card_channel")
        _channelChannelOnCardText = _document.createTextNode("%s" % self.channelOnCard)
        _channelChannelOnCardElement.appendChild(_channelChannelOnCardText)
        retVal.appendChild(_channelChannelOnCardElement)
        return retVal


class MachineInfo(object):

    def __init__(self, machineName, pythonVersion, osType):
        self.machineName = machineName
        self.pythonVersion = pythonVersion
        self.osType = osType

    def __str__(self):
        retVal = "Machine name: %s\n" % self.machineName
        retVal += "Python version: %s\n" % self.pythonVersion
        retVal += "OS: %s\n" % self.osType
        retVal += "CANLIB: %s\n" % GetCANLIBInfo()
        retVal += "pycanlib version: %s\n" % __version__
        return retVal

    def ToXML(self):
        _document = minidom.Document()
        retVal = _document.createElement("machine_info")
        _machineNameElement = _document.createElement("name")
        _machineNameText = _document.createTextNode(self.machineName)
        _machineNameElement.appendChild(_machineNameText)
        retVal.appendChild(_machineNameElement)
        _machineOSElement = _document.createElement("os")
        _machineOSText = _document.createTextNode(self.osType)
        _machineOSElement.appendChild(_machineOSText)
        retVal.appendChild(_machineOSElement)
        _machinePythonElement = _document.createElement("python_version")
        _machinePythonText = _document.createTextNode(self.pythonVersion)
        _machinePythonElement.appendChild(_machinePythonText)
        retVal.appendChild(_machinePythonElement)
        _machineCANLIBElement = _document.createElement("canlib_version")
        _machineCANLIBText = _document.createTextNode(GetCANLIBInfo())
        _machineCANLIBElement.appendChild(_machineCANLIBText)
        retVal.appendChild(_machineCANLIBElement)
        _machinePycanlibElement = _document.createElement("pycanlib_version")
        _machinePycanlibText = _document.createTextNode(__version__)
        _machinePycanlibElement.appendChild(_machinePycanlibText)
        retVal.appendChild(_machinePycanlibElement)
        return retVal

def GetHostMachineInfo():#pragma: no cover
    if sys.platform == "win32":
        machineName = os.getenv("COMPUTERNAME")
    else:
        machineName = os.getenv("HOSTNAME")
    pythonVersion = sys.version[:sys.version.index(" ")]
    return MachineInfo(machineName, pythonVersion, sys.platform)


def GetCANLIBInfo():#pragma: no cover
    _canlibProdVer32 = \
      canlib.canGetVersionEx(canlib.canVERSION_CANLIB32_PRODVER32)
    _majorVerNo = (_canlibProdVer32 & 0x00FF0000) >> 16
    _minorVerNo = (_canlibProdVer32 & 0x0000FF00) >> 8
    if (_canlibProdVer32 & 0x000000FF) != 0:
        _minorVerLetter = "%c" % (_canlibProdVer32 & 0x000000FF)
    else:
        _minorVerLetter = ""
    return "%d.%d%s" % (_majorVerNo, _minorVerNo, _minorVerLetter)


class Bus(object):

    def __init__(self, channel=0, flags=0, speed=1000000, tseg1=1, tseg2=0,
                 sjw=1, noSamp=1, driverMode=canlib.canDRIVER_NORMAL,
                 name="default"):
        self.name = name
        busClassLogger.info("Getting read handle for new Bus instance '%s'" %
          self.name)
        self.readHandle = _GetHandle(channel, flags, readHandleRegistry)
        busClassLogger.info("Read handle for Bus '%s' is %d" %
                            (self.name, self.readHandle.canlibHandle))
        busClassLogger.info("Getting write handle for new Bus instance '%s'" %
                            self.name)
        self.writeHandle = _GetHandle(channel, flags, writeHandleRegistry)
        busClassLogger.info("Write handle for Bus '%s' is %s" %
                            (self.name, self.writeHandle.canlibHandle))
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
        canlib.canSetDriverMode(self.readHandle.canlibHandle, driverMode,
          canstat.canTRANSCEIVER_RESNET_NA)
        if driverMode != canlib.canDRIVER_SILENT:
            canlib.canGetBusParams(self.writeHandle.canlibHandle,
              ctypes.byref(_oldSpeed), ctypes.byref(_oldTseg1),
              ctypes.byref(_oldTseg2), ctypes.byref(_oldSJW),
              ctypes.byref(_oldSampleNo), ctypes.byref(_oldSyncMode))
            if ((speed != _oldSpeed.value) or (tseg1 != _oldTseg1.value) or
                (tseg2 != _oldTseg2.value) or (sjw != _oldSJW.value) or
                (noSamp != _oldSampleNo.value)):
                canlib.canBusOff(self.writeHandle.canlibHandle)
                canlib.canSetBusParams(self.writeHandle.canlibHandle, speed,
                                       tseg1, tseg2, sjw, noSamp, 0)
                canlib.canBusOn(self.writeHandle.canlibHandle)
            canlib.canSetDriverMode(self.writeHandle.canlibHandle, driverMode,
              canstat.canTRANSCEIVER_RESNET_NA)
        self.driverMode = driverMode
        self.rxQueue = Queue.Queue(0)
        self.timerOffset = self.readHandle.ReadTimer()
        self.readHandle.AddListener(self)

    def Read(self):
        try:
            return self.rxQueue.get_nowait()
        except Queue.Empty:
            busClassLogger.debug("Bus '%s': No messages available" % self.name)
            return None

    def AddListener(self, listener):
        self.readHandle.AddListener(listener)
        listener.SetBus(self)

    def Write(self, msg):
        busClassLogger.debug("Bus '%s': Entering Write()" % self.name)
        if self.driverMode != canlib.canDRIVER_SILENT:
            busClassLogger.debug("Bus '%s': writing message %s" % (self.name, msg))
            self.writeHandle.Write(msg)
        busClassLogger.debug("Bus '%s': Leaving Write()" % self.name)

    def ReadTimer(self):
        return (float(self.readHandle.ReadTimer() - self.timerOffset) /
          TIMER_TICKS_PER_SECOND)

    def OnMessageReceived(self, msg):
        self.rxQueue.put_nowait(msg)

    def _GetDeviceDescription(self):#pragma: no cover
        return self.readHandle.GetDeviceDescription()

    def _GetDeviceManufacturerName(self):#pragma: no cover
        return self.readHandle.GetDeviceManufacturerName()

    def _GetDeviceFirmwareVersion(self):#pragma: no cover
        return self.readHandle.GetDeviceFirmwareVersion()

    def _GetDeviceHardwareVersion(self):#pragma: no cover
        return self.readHandle.GetDeviceHardwareVersion()

    def _GetDeviceCardSerial(self):#pragma: no cover
        return self.readHandle.GetDeviceCardSerial()

    def _GetDeviceTransceiverSerial(self):#pragma: no cover
        return self.readHandle.GetDeviceTransceiverSerial()

    def _GetDeviceCardNumber(self):#pragma: no cover
        return self.readHandle.GetDeviceCardNumber()

    def _GetDeviceChannelOnCard(self):#pragma: no cover
        return self.readHandle.GetDeviceChannelOnCard()

    def _GetDeviceTransceiverType(self):#pragma: no cover
        return self.readHandle.GetDeviceTransceiverType()

    def GetChannelInfo(self):#pragma: no cover
        return ChannelInfo(self.readHandle.channel,
                           self._GetDeviceDescription(),
                           self._GetDeviceManufacturerName(),
                           self._GetDeviceFirmwareVersion(),
                           self._GetDeviceHardwareVersion(),
                           self._GetDeviceCardSerial(),
                           self._GetDeviceTransceiverSerial(),
                           self._GetDeviceTransceiverType(),
                           self._GetDeviceCardNumber(),
                           self._GetDeviceChannelOnCard())

    def GetStatistics(self):
        return self.readHandle.GetStatistics()

@atexit.register
def Cleanup():#pragma: no cover
    canModuleLogger.info("Waiting for receive callbacks to complete...")
    for _handle in readHandleRegistry.values():
        canModuleLogger.info("\tHandle %d..." % _handle.canlibHandle)
        _handle.receiveCallbackEnabled = False
        while _handle.reading: pass
        canModuleLogger.info("\tOK")
    canModuleLogger.info("Waiting for transmit callbacks to complete...")
    for _handle in writeHandleRegistry.values():
        canModuleLogger.info("\tHandle %d..." % _handle.canlibHandle)
        _handle.transmitCallbackEnabled = False
        while _handle.writing: pass
        canModuleLogger.info("\tOK")
    canModuleLogger.info("Clearing receive callbacks...")
    for _handleNumber in readHandleRegistry.keys():
        canModuleLogger.info("\tHandle %d" % _handle.canlibHandle)
        canlib.kvSetNotifyCallback(_handleNumber, None, None, 0)
        canlib.canFlushReceiveQueue(_handleNumber)
    canModuleLogger.info("Clearing transmit callbacks...")
    for _handleNumber in writeHandleRegistry.keys():
        canModuleLogger.info("\tHandle %d" % _handle.canlibHandle)
        canlib.kvSetNotifyCallback(_handleNumber, None, None, 0)
        canlib.canFlushTransmitQueue(_handleNumber)

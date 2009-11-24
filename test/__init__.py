import ctypes
import logging
import nose
import random
import sys
import time
import types

sys.path.append("../pycanlib")

import canlib
import CANLIBErrorHandlers
import canstat
import CAN


testLogger = logging.getLogger("pycanlib.test")


def setup():
    canlib.canInitializeLibrary()
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    numChannels = _numChannels.value
    #We need to verify that all of pycanlib's functions operate correctly
    #on both virtual and physical channels, so we need to find at least one
    #of each to test with
    physicalChannels = []
    virtualChannels = []
    for _channel in xrange(numChannels):
        _cardType = ctypes.c_int(0)
        canlib.canGetChannelData(_channel,
          canlib.canCHANNELDATA_CARD_TYPE, ctypes.byref(_cardType), 4)
        if _cardType.value == canlib.canHWTYPE_VIRTUAL:
            virtualChannels.append(_channel)
        elif _cardType.value != canlib.canHWTYPE_NONE:
            physicalChannels.append(_channel)
    if (len(virtualChannels) == 0):
        raise Exception("No virtual channels available for testing")
    elif(len(physicalChannels) == 0):
        raise Exception("No physical channels available for testing")
    testLogger.debug("numChannels = %d" % numChannels)
    testLogger.debug("virtualChannels = %s" % virtualChannels)
    testLogger.debug("physicalChannels = %s" % physicalChannels)


def testShallCreateInfoMessageObject():
    _msgObject = None
    _msgObject = CAN.InfoMessage()
    assert (_msgObject != None)
    assert ("timestamp" in _msgObject.__dict__.keys())
    assert ("info" in _msgObject.__dict__.keys())


def testShallNotAcceptInvalidTimestamps():
    for timestamp in ["foo", -5, -1.0, 0.0, 1, 1.0, 2.5, 10000, 10000.2]:
        yield isTimestampValid, timestamp


def isTimestampValid(timestamp):
    _msgObject = None
    try:
        _msgObject = CAN.InfoMessage(timestamp=timestamp)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.InfoMessage", exc_info=True)
        testLogger.debug(e.__str__())
    if isinstance(timestamp, types.FloatType) and (timestamp >= 0):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)


def testShallProvideStringRepresentationOfInfoMessage():
    timestamps = range(0, 10000, 503)
    infoStrings = ["info string 1", "info string 2", "not an info string",
                   "another string", None]
    for timestamp in timestamps:
        for infoString in infoStrings:
            yield checkInfoMsgStringRep, (float(timestamp) / 10), infoString


def checkInfoMsgStringRep(timestamp, infoString):
    _msgObject = None
    _msgObject = CAN.InfoMessage(timestamp, infoString)
    assert (_msgObject != None)
    assert (_msgObject.timestamp == timestamp)
    assert (_msgObject.info == infoString)
    if infoString != None:
        assert (_msgObject.__str__() == "%.6f\t%s" % (timestamp, infoString))
    else:
        assert (_msgObject.__str__() == "%.6f" % timestamp)


def testShallCreateCANMessageObject():
    _msgObject = None
    _msgObject = CAN.Message()
    assert (_msgObject != None)
    assert ("timestamp" in _msgObject.__dict__.keys())
    assert ("deviceID" in _msgObject.__dict__.keys())
    assert ("dlc" in _msgObject.__dict__.keys())
    assert ("data" in _msgObject.__dict__.keys())
    assert ("flags" in _msgObject.__dict__.keys())


def testShallNotAcceptInvalidDeviceIDs():
    for deviceID in ["foo", 0, 0.1, 10000, 0x0100, 2 ** 32]:
        yield isDeviceIDValid, deviceID


def isDeviceIDValid(deviceID):
    _msgObject = None
    try:
        _msgObject = CAN.Message(deviceID=deviceID)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.Message", exc_info=True)
        testLogger.debug(e.__str__())
    if isinstance(deviceID, types.IntType) and (deviceID in range(0, 2 ** 11)):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)


def testShallNotAcceptInvalidPayload():
    payloads = []
    payloads.append([])
    payloads.append([10000])
    payloads.append(["foo"])
    payloads.append([0, 0, 0, 0, 0, 0, 0, 0, 0])
    payloads.append([0, 100000])
    payloads.append([" ", 0])
    for payload in payloads:
        yield isPayloadValid, payload


def isPayloadValid(payload):
    _msgObject = None
    try:
        _msgObject = CAN.Message(data=payload)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.Message", exc_info=True)
        testLogger.debug(e.__str__())
    payloadValid = True
    if len(payload) not in range(0, 9):
        payloadValid = False
    for item in payload:
        if not isinstance(item, types.IntType):
            payloadValid = False
        elif item not in range(0, 256):
            payloadValid = False
    if payloadValid:
        assert (_msgObject != None)
        assert (_msgObject.data == payload)
    else:
        assert (_msgObject == None)


def testShallNotAcceptInvalidDLC():
    dlcs = ["foo", 0.25]
    for i in xrange(-2, 10):
        dlcs.append(i)
    for dlc in dlcs:
        yield isDLCValid, dlc


def isDLCValid(dlc):
    _msgObject = None
    try:
        _msgObject = CAN.Message(dlc=dlc)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.Message", exc_info=True)
        testLogger.debug(e.__str__())
    if dlc in range(0, 9):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)


def testShallNotAcceptInvalidFlags():
    flagsValues = ["foo", 0.25]
    for i in xrange(-2, 2):
        flagsValues.append(i)
    for i in xrange(2 ** 15 - 2, 2 ** 15 + 2):
        flagsValues.append(i)
    for i in xrange(2 ** 16 - 2, 2 ** 16 + 2):
        flagsValues.append(i)
    for flagsValue in flagsValues:
        yield areFlagsValid, flagsValue


def areFlagsValid(flags):
    _msgObject = None
    try:
        _msgObject = CAN.Message(flags=flags)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.Message", exc_info=True)
        testLogger.debug(e.__str__())
    if flags in range(0, 2 ** 16):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)


def testShallProvideStringRepresentationOfCANMessage():
    timestamps = [0.0, 1.23456, 9.9999999999, 1.06]
    dataArrays = [[1], [255], [0xb0, 0x81, 0x50]]
    dlcs = range(0, 9)
    flagsValues = [0, 1, 2 ** 15, 2 ** 16 - 1]
    deviceIDs = [0x0040, 0x0008, 0x0100]
    testData = []
    for timestamp in timestamps:
        for dataArray in dataArrays:
            for dlc in dlcs:
                for flags in flagsValues:
                    for deviceID in deviceIDs:
                        yield (checkCANMessageStringRepr, timestamp,
                               dataArray, dlc, flags, deviceID)


def checkCANMessageStringRepr(timestamp, dataArray, dlc, flags, deviceID):
    _msgObject = None
    try:
        _msgObject = CAN.Message(deviceID=deviceID, timestamp=timestamp,
                                 data=dataArray, dlc=dlc, flags=flags)
    except Exception as e:
        testLogger.debug("Exception thrown by CAN.Message", exc_info=True)
        testLogger.debug(e.__str__())
    assert (_msgObject != None)
    dataString = ("%s" % ' '.join([("%.2x" % byte) for byte in dataArray]))
    expectedStringRep = "%.6f\t%.4x\t%.4x\t%d\t%s" % (timestamp, deviceID,
                                                    flags, dlc, dataString)
    assert (_msgObject.__str__() == expectedStringRep)


def testShallCreateBusObject():
    _bus1 = None
    _bus2 = None
    try:
        _bus1 = CAN.Bus()
    except:
        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
    try:
        _bus2 = CAN.Bus()
    except:
        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
    assert (_bus1 != None)
    assert (_bus2 != None)
    testLogger.debug("_bus1.writeHandle.canlibHandle = %d" %
                     _bus1.writeHandle.canlibHandle)
    testLogger.debug("_bus2.writeHandle.canlibHandle = %d" %
                     _bus2.writeHandle.canlibHandle)
    assert (_bus1.writeHandle.canlibHandle == _bus2.writeHandle.canlibHandle)
    assert (_bus1.readHandle.canlibHandle == _bus2.readHandle.canlibHandle)


def testShallAcceptOnlyLegalChannelNumbers():
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    channelNumbers = ["foo", 0.25]
    for i in xrange(-3, _numChannels.value + 3):
        channelNumbers.append(i)
    for channelNumber in channelNumbers:
        yield checkChannelNumber, channelNumber, _numChannels.value


def checkChannelNumber(channelNumber, numChannels):
    _bus = None
    try:
        _bus = CAN.Bus(channel=channelNumber,
                       flags=canlib.canOPEN_ACCEPT_VIRTUAL)
    except:
        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
    if channelNumber in range(0, numChannels):
        assert (_bus != None)
    else:
        testLogger.debug("numChannels = %d" % numChannels)
        assert (_bus == None)


#def testShallAcceptOnlyLegalSegmentLengths():
#    segmentLengths = ["foo", 0.25]
#    for i in xrange(-1, 10):
#        segmentLengths.append(i)
#    for tseg1 in segmentLengths:
#        for tseg2 in segmentLengths:
#            yield checkSegmentLengths, tseg1, tseg2


#def checkSegmentLengths(tseg1, tseg2):
#    _bus = None
#    try:
#        _bus = CAN.Bus(tseg1=tseg1, tseg2=tseg2)
#    except:
#        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
#    if (isinstance(tseg1, types.IntType) and
#        isinstance(tseg2, types.IntType) and ((tseg1 + tseg2) < 16) and
#        (tseg1 >= 0) and (tseg2 >= 0)):
#        assert (_bus != None)
#    else:
#        assert (_bus == None)


def testShallNotAcceptInvalidBusFlags():
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    numChannels = _numChannels.value
    virtualChannels = []
    physicalChannels = []
    for _channel in xrange(numChannels):
        _cardType = ctypes.c_int(0)
        canlib.canGetChannelData(_channel,
          canlib.canCHANNELDATA_CARD_TYPE, ctypes.byref(_cardType), 4)
        if _cardType.value == canlib.canHWTYPE_VIRTUAL:
            virtualChannels.append(_channel)
        else:
            physicalChannels.append(_channel)
    testLogger.debug(virtualChannels)
    for _channel in virtualChannels:
        yield openVirtualChannelWithIncorrectFlags, _channel
    for _channel in virtualChannels:
        yield openChannelWithInvalidFlags, _channel
    for _channel in physicalChannels:
        yield openChannelWithInvalidFlags, _channel


def openVirtualChannelWithIncorrectFlags(channel):
    _bus = None
    try:
        _bus = CAN.Bus(channel=channel, flags=0)
    except CAN.InvalidBusParameterError as e:
        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
        testLogger.debug(e)
    assert (_bus == None)


def openChannelWithInvalidFlags(channel):
    _bus = None
    try:
        _bus = CAN.Bus(channel=channel, flags=0xFFFF)
    except CAN.InvalidBusParameterError as e:
        testLogger.debug("Exception thrown by CAN.Bus", exc_info=True)
        testLogger.debug(e)
    assert (_bus == None)

import ctypes
import logging
import nose
import sys
import types

sys.path.append("../pycanlib")
import canlib
import CANLIBErrorHandlers
import canstat
import CAN

def setup():
    canlib.canInitializeLibrary()


def testShallCreateInfoMessageObject():
    _msgObject = None
    try:
        _msgObject = CAN.InfoMessage()
    except:
        logging.debug("Exception thrown by CAN.InfoMessage", exc_info=True)
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
    except:
        logging.debug("Exception thrown by CAN.InfoMessage", exc_info=True)
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
            yield checkInfoMsgStringRep, float(timestamp)/10, infoString

def checkInfoMsgStringRep(timestamp, infoString):
    _msgObject = None
    try:
        _msgObject = CAN.InfoMessage(timestamp, infoString)
    except:
        logging.debug("Exception thrown by CAN.InfoMessage", exc_info=True)
    assert (_msgObject != None)
    assert (_msgObject.timestamp == timestamp)
    assert (_msgObject.info == infoString)
    if infoString != None:
        assert (_msgObject.__str__() == "%.6f\t%s" % (timestamp, infoString))
    else:
        assert (_msgObject.__str__() == "%.6f" % timestamp)

def testShallCreateCANMessageObject():
    _msgObject = None
    try:
        _msgObject = CAN.Message()
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
    assert (_msgObject != None)
    assert ("timestamp" in _msgObject.__dict__.keys())
    assert ("deviceID" in _msgObject.__dict__.keys())
    assert ("dlc" in _msgObject.__dict__.keys())
    assert ("data" in _msgObject.__dict__.keys())
    assert ("flags" in _msgObject.__dict__.keys())

def testShallNotAcceptInvalidDeviceIDs():
    for deviceID in ["foo", 0, 0.1, 10000, 0x0100, 2**32]:
        yield isDeviceIDValid, deviceID

def isDeviceIDValid(deviceID):
    _msgObject = None
    try:
        _msgObject = CAN.Message(deviceID=deviceID)
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
    if isinstance(deviceID, types.IntType) and (deviceID in range(0, 2**11)):
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
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
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
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
    if dlc in range(0, 9):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)

def testShallNotAcceptInvalidFlags():
    flagsValues = ["foo", 0.25]
    for i in xrange(-2, 2):
        flagsValues.append(i)
    for i in xrange(2**15-2, 2**15+2):
        flagsValues.append(i)
    for i in xrange(2**16-2, 2**16+2):
        flagsValues.append(i)
    for flagsValue in flagsValues:
        yield areFlagsValid, flagsValue

def areFlagsValid(flags):
    _msgObject = None
    try:
        _msgObject = CAN.Message(flags=flags)
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
    if flags in range(0, 2**16):
        assert (_msgObject != None)
    else:
        assert (_msgObject == None)

def testShallProvideStringRepresentationOfCANMessage():
    timestamps = [0.0, 1.23456, 9.9999999999, 1.06]
    dataArrays = [[1], [255], [0xb0, 0x81, 0x50]]
    dlcs = range(0, 9)
    flagsValues = [0, 1, 2*15, 2*16-1]
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
    except:
        logging.debug("Exception thrown by CAN.Message", exc_info=True)
    assert (_msgObject != None)
    dataString = ("%s" % ' '.join([("%.2x" % byte) for byte in dataArray]))
    expectedStringRep = "%.6f\t%.4x\t%.4x\t%d\t%s" % (timestamp, deviceID,
                                                    flags, dlc, dataString)
    logging.debug(expectedStringRep)
    logging.debug(_msgObject.__str__())
    assert (_msgObject.__str__() == expectedStringRep)

"""
def testShallCreateBusObject():
    _bus1 = None
    _bus2 = None
    try:
        _bus1 = CAN.Bus()
    except:
        logging.debug("Exception thrown by CAN.Bus", exc_info=True)
    try:
        _bus2 = CAN.Bus()
    except:
        logging.debug("Exception thrown by CAN.Bus", exc_info=True)
    assert (_bus1 != None)
    assert (_bus2 != None)
    assert (_bus1.writeHandle == _bus2.writeHandle)
    assert (_bus1.readHandle == _bus2.readHandle)


def testShallAcceptOnlyLegalChannelNumbers():
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    numChannels = _numChannels.value
    channelNumbers = ["foo", 0.25]
    for i in xrange(-3, numChannels + 3):
        channelNumbers.append(i)
    for channelNumber in channelNumbers:
        yield checkChannelNumber, channelNumber


def checkChannelNumber(channelNumber):
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    numChannels = _numChannels.value
    _bus = None
    try:
        _bus = CAN.Bus(channel=channelNumber)
    except:
        logging.debug("Exception thrown by CAN.Bus", exc_info=True)
    if channelNumber in range(0, numChannels):
        assert (_bus != None)
    else:
        assert (_bus == None)


def testShallAcceptOnlyLegalSegmentLengths():
    segmentLengths = ["foo", -1, 0, 1, 2, 253, 254, 255, 256, 257]
    for tseg1 in segmentLengths:
        for tseg2 in segmentLengths:
            yield checkSegmentLengths, tseg1, tseg2


def checkSegmentLengths(tseg1, tseg2):
    _bus = None
    try:
        _bus = CAN.Bus(tseg1=tseg1, tseg2=tseg2)
    except:
        logging.debug("Exception thrown by CAN.Bus", exc_info=True)
    if (tseg1 in range(1, 256)) and (tseg2 in range(0, 256)):
        assert (_bus != None)
    else:
        assert (_bus == None)
"""

def teardown():
#    for handle in CAN.readHandleList:
#        if CANLIBErrorHandlers._HandleValid(handle.handle):
#            canlib.kvSetNotifyCallback(handle.handle, None,
#                                       ctypes.c_void_p(0), 0)
#            canlib.canClose(handle.handle)
#    for handle in CAN.writeHandleList:
#        if CANLIBErrorHandlers._HandleValid(handle.handle):
#            canlib.kvSetNotifyCallback(handle.handle, None,
#                                       ctypes.c_void_p(0), 0)
#            canlib.canClose(handle.handle)
    canlib.canUnloadLibrary()

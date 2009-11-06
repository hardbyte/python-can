import ctypes, sys, types, unittest

sys.path.append("..")

import CAN
import canlib

BUS_TYPE_PHYSICAL = 0
BUS_TYPE_VIRTUAL = 1

class pycanlib_TestHarness(unittest.TestCase):

    def setUp(self):
        canlib.canInitializeLibrary()
        _numChannels = ctypes.c_int(0)
        canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
        self.numChannels = _numChannels.value
        #We need to verify that all of pycanlib's functions operate correctly
        #on both virtual and physical channels, so we need to find at least one
        #of each to test with
        self.physicalChannels = []
        self.virtualChannels = []
        for _channel in xrange(self.numChannels):
            _cardType = ctypes.c_int(0)
            canlib.canGetChannelData(_channel,
              canlib.canCHANNELDATA_CARD_TYPE, ctypes.byref(_cardType), 4)
            if _cardType.value == canlib.canHWTYPE_VIRTUAL:
                self.virtualChannels.append(_channel)
            elif _cardType.value != canlib.canHWTYPE_NONE:
                self.physicalChannels.append(_channel)
        if (len(self.virtualChannels) == 0):
            raise Exception("No virtual channels available for testing")
        elif(len(self.physicalChannels) == 0):
            print "Warning: no physical channels are available for testing -",
            print " this test run has only used virtual channels to verify the",
            print " pycanlib code"

    def testREQ_ShallCreateBusObject(self, busType=BUS_TYPE_PHYSICAL):
        busObject = None
        for _channel in range(0, self.numChannels):
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                try:
                    #default bus object, with defined channel and flags value
                    #allowing opening of a virtual channel
                    busObject = CAN.Bus(channel=_channel,
                      flags=canlib.canOPEN_ACCEPT_VIRTUAL)
                except CAN.InvalidBusParameterException as e:
                    print e
                self.assert_(busObject != None)
                self.assert_(busObject.channel == _channel)

    def testREQ_ShallAcceptOnlyLegalChannelNumbers(self, busType=BUS_TYPE_PHYSICAL):
        for _channel in xrange(-3, self.numChannels+5):
            print _channel
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                e = None
                busObject = None
                try:
                    print "creating"
                    busObject = CAN.Bus(channel=_channel,
                      flags=canlib.canOPEN_ACCEPT_VIRTUAL)
                    print "done"
                except CAN.InvalidBusParameterException as e:
                    print e
                if _channel in range(0, self.numChannels):
                    self.assert_(busObject != None)
                    self.assert_(busObject.channel == _channel)
                else:
                    self.assert_(busObject == None)
                    self.assert_(isinstance(e, CAN.InvalidBusParameterException))
                    self.assert_(e.parameterName == "channel")
                    self.assert_(e.parameterValue == _channel)

    """
    def testREQ_ShallAcceptOnlyLegalBusSpeeds(self, busType=BUS_TYPE_PHYSICAL):#BROKEN
        for _channel in xrange(self.numChannels):
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                for _speed in ["foo", -1, 0, 1, 10**5, 10**6, 10**6+1]:
                    busObject = None
                    try:
                        busObject = CAN.Bus(channel=_channel,
                          flags=KvaserAPI.canOPEN_VIRTUAL, speed=_speed)
                    except Exception as e:
                        pass
                    if (isinstance(_speed, types.IntType) and
                      (_speed in range(10, 10**6+1))):
                        self.assert_(busObject != None)
                        self.assert_(busObject.speed == _speed)
                    else:
                        self.assert_(busObject == None)
                        self.assert_(isinstance(e, CAN.InvalidBusSpeedException))
                        self.assert_(e.speed == _speed)
                    if busObject != None:
                        busObject.Cleanup()
#                        del busObject

    def testREQ_ShallAcceptOnlyLegalSegmentLengths(self, busType=BUS_TYPE_PHYSICAL):#BROKEN
        testValues = ["foo", -1, 0, 5, 8, 9, 10, 11, 12]
        for _channel in xrange(self.numChannels):
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                for _tseg1 in testValues:
                    for _tseg2 in testValues:
                        busObject = None
                        try:
                            busObject = CAN.Bus(channel=_channel,
                              flags=KvaserAPI.canOPEN_VIRTUAL, tseg1=_tseg1,
                              tseg2=_tseg2)
                        except Exception as e:
                            pass
                        if (isinstance(_tseg1, types.IntType) and
                          isinstance(_tseg2, types.IntType) and
                          (_tseg1 in range(0, 11)) and
                          (_tseg2 in range(0, 11))):
                            self.assert_(busObject != None)
                            self.assert_(busObject.tseg1 == _tseg1)
                            self.assert_(busObject.tseg2 == _tseg2)
                        else:
                            self.assert_(busObject == None)
                            self.assert_(isinstance(e,
                              CAN.InvalidSegmentLengthException))
                            self.assert_(e.tseg1 == _tseg1)
                            self.assert_(e.tseg2 == _tseg2)
                        if busObject != None:
                            busObject.Cleanup()
#                            del busObject

    def testREQ_ShallAcceptOnlyLegalSyncJumpWidths(self, busType=BUS_TYPE_PHYSICAL):#less broken
        testValues = ["foo", 0, 1, 2, 3, 4, 5, 6]
        for _channel in xrange(self.numChannels):
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                for _sjw in testValues:
                    busObject = None
                    try:
                        busObject = CAN.Bus(channel=_channel,
                          flags=KvaserAPI.canOPEN_VIRTUAL, sjw=_sjw)
                    except Exception as e:
                        pass
                    if _sjw in range(1, 5):
                        self.assert_(busObject != None)
                        self.assert_(busObject.sjw == _sjw)
                    else:
                        self.assert_(busObject == None)
                        self.assert_(isinstance(e, CAN.InvalidSJWException))
                        self.assert_(e.sjw == _sjw)
                    if busObject != None:
                        busObject.Cleanup()
#                        del busObject

    def testREQ_ShallAcceptOnlyLegalSamplingPoints(self, busType=BUS_TYPE_PHYSICAL):
        testValues = ["foo", 0, 1, 2, 3, 4]
        for _channel in xrange(self.numChannels):
            if (((busType == BUS_TYPE_PHYSICAL) and
              (_channel in self.physicalChannels)) or
              ((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                for _noSamp in testValues:
                    busObject = None
                    try:
                        busObject = CAN.Bus(channel=_channel,
                          flags=KvaserAPI.canOPEN_VIRTUAL, noSamp=_noSamp)
                    except Exception as e:
                        pass
                    if _noSamp in [1, 3]:
                        self.assert_(busObject != None)
                        self.assert_(busObject.noSamp == _noSamp)
                    else:
                        self.assert_(busObject == None)
                        self.assert_(isinstance(e, CAN.InvalidSamplingPointsException))
                        self.assert_(e.noSamp == _noSamp)
                    if busObject != None:
                        busObject.Cleanup()
#                        del busObject

    def testREQ_ShallAllowConnectionToVirtualBus(self):#invalid channel number
        self.testREQ_ShallCreateBusObject(busType=BUS_TYPE_VIRTUAL)
        self.testREQ_ShallAcceptOnlyLegalChannelNumbers(busType=BUS_TYPE_VIRTUAL)
        self.testREQ_ShallAcceptOnlyLegalBusSpeeds(busType=BUS_TYPE_VIRTUAL)
        self.testREQ_ShallAcceptOnlyLegalSegmentLengths(busType=BUS_TYPE_VIRTUAL)
        self.testREQ_ShallAcceptOnlyLegalSyncJumpWidths(busType=BUS_TYPE_VIRTUAL)
        self.testREQ_ShallAcceptOnlyLegalSamplingPoints(busType=BUS_TYPE_VIRTUAL)
#        self.testREQ_ShallAllowWritingToBus_ShallAllowReadingFromBus(busType=BUS_TYPE_VIRTUAL)

    def testREQ_ShallCreateInfoMessageObject(self):
        messageObject = None
        try:
            messageObject = CAN.InfoMessage()
        except:
            pass
        self.assert_(messageObject != None)
        self.assert_("timestamp" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.timestamp, types.IntType))
        self.assert_("infoString" in messageObject.__dict__.keys())
        self.assert_(messageObject.infoString == None)
        messageObject = None
        try:
            messageObject = CAN.InfoMessage(infoString="info string")
        except:
            pass
        self.assert_(messageObject != None)
        self.assert_("timestamp" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.timestamp, types.IntType))
        self.assert_("infoString" in messageObject.__dict__.keys())
        self.assert_(messageObject.infoString == "info string")
    """

    def testREQ_ShallCreateCANMessageObject(self):
        messageObject = None
        try:
            messageObject = CAN.Message()
        except CAN.InvalidMessageParameterException as e:
            print e
        self.assert_(messageObject != None)
        self.assert_("timestamp" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.timestamp, types.IntType))
        self.assert_("deviceID" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.deviceID, types.IntType))
        self.assert_("data" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.data, types.ListType))
        self.assert_("dlc" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.dlc, types.IntType))
        self.assert_("flags" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.flags, types.IntType))

    def testREQ_ShallNotAcceptNegativeTimestamps(self):
        for _timestamp in ["foo", -10, 0, 1, 10, -5, 100]:
            messageObject = None
            try:
                messageObject = CAN.Message(timestamp=_timestamp)
            except CAN.InvalidMessageParameterException as e:
                print e
            if isinstance(_timestamp, types.IntType) and (_timestamp >= 0):
                self.assert_(messageObject != None)
                self.assert_(messageObject.timestamp == _timestamp)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "timestamp")
                self.assert_(e.parameterValue == _timestamp)
            try:
                messageObject = CAN.InfoMessage(timestamp=_timestamp)
            except CAN.InvalidMessageParameterException as e:
                print e
            if isinstance(_timestamp, types.IntType) and (_timestamp >= 0):
                self.assert_(messageObject != None)
                self.assert_(messageObject.timestamp == _timestamp)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "timestamp")
                self.assert_(e.parameterValue == _timestamp)

    def testREQ_ShallNotAcceptInvalidDeviceIDs(self):
        for _deviceID in ["foo", -2, -1, 0, 1, 2, 2**10, 2**11-2,
          2**11-1, 2**11, 2**11+1]:
            messageObject = None
            try:
                messageObject = CAN.Message(deviceID=_deviceID)
            except CAN.InvalidMessageParameterException as e:
                print e
            if isinstance(_deviceID, types.IntType) and _deviceID in range(0, 2**11):
                self.assert_(messageObject != None)
                self.assert_(messageObject.deviceID == _deviceID)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "deviceID")
                self.assert_(e.parameterValue == _deviceID)

    def testREQ_ShallNotAcceptInvalidPayload(self):
        payloads = []
        #no data - should pass
        payloads.append([])
        #9 byte payload - should fail
        payloads.append([0, 1, 2, 3, 4, 5, 6, 7, 8])
        #acceptable length, but data out of range
        for length in xrange(8):
            _payload = []
            for _length in xrange(length-1):
                _payload.append(0)
            _payload.append(256)
            payloads.append(_payload)
        for length in xrange(8):
            _payload = []
            for _length in xrange(length-1):
                _payload.append(0)
            _payload.append(-1)
            payloads.append(_payload)
        for length in xrange(8):
            _payload = []
            for _length in xrange(length-1):
                _payload.append(0)
            _payload.append(-2)
            payloads.append(_payload)
        #acceptable length, but data not all integers
        for length in xrange(8):
            _payload = []
            for _length in xrange(length-1):
                _payload.append(0)
            _payload.append("foo")
            payloads.append(_payload)
        for _payload in payloads:
            messageObject = None
            try:
                messageObject = CAN.Message(data=_payload)
            except CAN.InvalidMessageParameterException as e:
                print e
            badMessage = False
            for item in _payload:
                if not isinstance(item, types.IntType):
                    badMessage = True
                    break
                if item not in range(0, 255):
                    badMessage = True
            if len(_payload) not in range(0, 8):
                badMessage = True
            if badMessage:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e, CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "data")
                self.assert_(e.parameterValue == _payload)
            else:
                self.assert_(messageObject != None)
                self.assert_(messageObject.data == _payload)

    def testREQ_ShallNotAcceptInvalidDLC(self):
        _testValues = ["foo"]
        for i in xrange(-3, 11):
            _testValues.append(i)
        for _dlc in _testValues:
            messageObject = None
            try:
                messageObject = CAN.Message(dlc=_dlc)
            except CAN.InvalidMessageParameterException as e:
                print e
            if isinstance(_dlc, types.IntType) and _dlc in range(0, 9):
                self.assert_(messageObject != None)
                self.assert_(messageObject.dlc == _dlc)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e, CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "dlc")
                self.assert_(e.parameterValue == _dlc)

    def testREQ_ShallNotAcceptInvalidFlags(self):
        _testValues = ["foo", -2, -1, 0, 2**15, 2**16-2, 2**16-1, 2**16,
          2**16+1]
        for _flags in _testValues:
            messageObject = None
            try:
                messageObject = CAN.Message(flags=_flags)
            except CAN.InvalidMessageParameterException as e:
                pass
            if isinstance(_flags, types.IntType) and _flags in range(0, 2**16):
                self.assert_(messageObject != None)
                self.assert_(messageObject.flags == _flags)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e, CAN.InvalidMessageParameterException))
                self.assert_(e.parameterName == "flags")
                self.assert_(e.parameterValue == _flags)

    def testREQ_ShallProvideStringRepresentationOfCANMessage(self):
        stringRepresentations = []
        messages = []
        messages.append(CAN.Message())
        stringRepresentations.append("0.000000\t0000\t0000\t0")
        messages.append(CAN.Message(deviceID=0x0008))
        stringRepresentations.append("0.000000\t0008\t0000\t0")
        messages.append(CAN.Message(data=[1, 2, 3]))
        stringRepresentations.append("0.000000\t0000\t0000\t0\t01 02 03")
        messages.append(CAN.Message(data=[1, 2, 3], dlc=3))
        stringRepresentations.append("0.000000\t0000\t0000\t3\t01 02 03")
        messages.append(CAN.Message(flags=0x0123))
        stringRepresentations.append("0.000000\t0000\t0123\t0")
        messages.append(CAN.Message(timestamp=1.234567))
        stringRepresentations.append("1.234567\t0000\t0000\t0")
        for _msg, _stringRep in zip(messages, stringRepresentations):
            self.assert_(_msg.__str__() == _stringRep)

    def testREQ_ShallProvideStringRepresentationOfInfoMessage(self):
        stringRepresentations = []
        messages = []
        messages.append(CAN.InfoMessage())
        stringRepresentations.append("0.000000")
        messages.append(CAN.InfoMessage(timestamp=1.234567))
        stringRepresentations.append("1.234567")
        messages.append(CAN.InfoMessage(infoString="this is an info string"))
        stringRepresentations.append("0.000000\tthis is an info string")
        messages.append(CAN.InfoMessage(timestamp=2.345678, infoString="this is another info string"))
        stringRepresentations.append("2.345678\tthis is another info string")
        for _msg, _stringRep in zip(messages, stringRepresentations):
            self.assert_(_msg.__str__() == _stringRep)

"""
    def testREQ_ShallAllowWritingToBus_ShallAllowReadingFromBus(self, busType=BUS_TYPE_PHYSICAL):
        for _channel in xrange(self.numChannels):
#            if (((busType == BUS_TYPE_PHYSICAL) and
#              (_channel in self.physicalChannels)) or
             if (((busType == BUS_TYPE_VIRTUAL) and
              (_channel in self.virtualChannels))):
                bus = CAN.Bus(channel=_channel, speed=105263, tseg1=10,
                  tseg2=8, sjw=4, noSamp=1)
                messages = []
                receivedMessages = []
                messages.append(CAN.Message())
                receivedMessages.append(CAN.Message())
                messages.append(CAN.Message(deviceID=0x0010))
                receivedMessages.append(CAN.Message(deviceID=0x0010))
                messages.append(CAN.Message(deviceID=0x0010, data=[1, 2, 3]))
                receivedMessages.append(CAN.Message(deviceID=0x0010, data=[1, 2, 3]))
                messages.append("Not a CAN message")
                messages.append(1)
                messages.append(CAN.Message(deviceID=0x0010, data=[1, 2, 3], dlc=3))
                receivedMessages.append(CAN.Message(deviceID=0x0010, data=[1, 2, 3], dlc=3))
                messages.append(CAN.Message(deviceID=0x0010, flags=0x0123))
                receivedMessages.append(CAN.Message(deviceID=0x0010, flags=0x0123))
                messages.append(CAN.Message(deviceID=0x0010, timestamp=1.234567))
                receivedMessages.append(CAN.Message(deviceID=0x0010, timestamp=1.234567))
                for message in messages:
                    bus.Write(message)
                receivedMessage = bus.Read()
                actualReceivedMessages = []
                while len(actualReceivedMessages) != len(receivedMessages):
                    if receivedMessage != None:
                        if receivedMessage.deviceID == 0x0010:
                            actualReceivedMessages.append(receivedMessage)
                    receivedMessage = bus.Read()
                for (expected, actual) in zip(receivedMessages, actualReceivedMessages):
                    self.assert_(expected.timestamp == actual.timestamp)
                    self.assert_(expected.deviceID == actual.deviceID)
                    self.assert_(expected.data == actual.data)
                    self.assert_(expected.dlc == actual.dlc)
                    self.assert_(expected.flags == actual.flags)
                del bus
"""
if __name__ == "__main__":
    unittest.main()

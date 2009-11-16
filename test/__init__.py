import ctypes
import sys
import types
import unittest

sys.path.append("../pycanlib")

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
            print " this test run has only used virtual channels to verify",
            print " the pycanlib code"

    def tearDown(self):
        canlib.canUnloadLibrary()

    def testREQ_ShallCreateInfoMessageObject(self):
        print
        messageObject = None
        messageObject = CAN.InfoMessage()
        self.assert_(messageObject != None)
        self.assert_("timestamp" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.timestamp, types.IntType))
        self.assert_("infoString" in messageObject.__dict__.keys())
        self.assert_(messageObject.infoString == None)
        messageObject = None
        messageObject = CAN.InfoMessage(infoString="info string")
        self.assert_(messageObject != None)
        self.assert_("timestamp" in messageObject.__dict__.keys())
        self.assert_(isinstance(messageObject.timestamp, types.IntType))
        self.assert_("infoString" in messageObject.__dict__.keys())
        self.assert_(messageObject.infoString == "info string")

    def testREQ_ShallCreateCANMessageObject(self):
        print
        messageObject = None
        messageObject = CAN.Message()
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
        print
        for _timestamp in ["foo", -10, 0, 1, 10, -5, 100]:
            messageObject = None
            try:
                messageObject = CAN.Message(timestamp=_timestamp)
            except CAN.InvalidMessageParameterError as e:
                print e
            if isinstance(_timestamp, types.IntType) and (_timestamp >= 0):
                self.assert_(messageObject != None)
                self.assert_(messageObject.timestamp == _timestamp)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "timestamp")
                self.assert_(e.parameterValue == _timestamp)
            try:
                messageObject = CAN.InfoMessage(timestamp=_timestamp)
            except CAN.InvalidMessageParameterError as e:
                print e
            if isinstance(_timestamp, types.IntType) and (_timestamp >= 0):
                self.assert_(messageObject != None)
                self.assert_(messageObject.timestamp == _timestamp)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "timestamp")
                self.assert_(e.parameterValue == _timestamp)

    def testREQ_ShallNotAcceptInvalidDeviceIDs(self):
        print
        for _deviceID in ["foo", -2, -1, 0, 1, 2, 2 ** 10, (2 ** 11) - 2,
          (2 ** 11) - 1, 2 ** 11, (2 ** 11) + 1]:
            messageObject = None
            try:
                messageObject = CAN.Message(deviceID=_deviceID)
            except CAN.InvalidMessageParameterError as e:
                print e
            if isinstance(_deviceID, types.IntType) and \
               _deviceID in range(0, 2 ** 11):
                self.assert_(messageObject != None)
                self.assert_(messageObject.deviceID == _deviceID)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e,
                  CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "deviceID")
                self.assert_(e.parameterValue == _deviceID)

    def testREQ_ShallNotAcceptInvalidPayload(self):
        print
        payloads = []
        payloads.append([])
        payloads.append([0, 1, 2, 3, 4, 5, 6, 7, 8])
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
            except CAN.InvalidMessageParameterError as e:
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
                self.assert_(isinstance(e, CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "data")
                self.assert_(e.parameterValue == _payload)
            else:
                self.assert_(messageObject != None)
                self.assert_(messageObject.data == _payload)

    def testREQ_ShallNotAcceptInvalidDLC(self):
        print
        _testValues = ["foo"]
        for i in xrange(-3, 11):
            _testValues.append(i)
        for _dlc in _testValues:
            messageObject = None
            try:
                messageObject = CAN.Message(dlc=_dlc)
            except CAN.InvalidMessageParameterError as e:
                print e
            if isinstance(_dlc, types.IntType) and _dlc in range(0, 9):
                self.assert_(messageObject != None)
                self.assert_(messageObject.dlc == _dlc)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e, CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "dlc")
                self.assert_(e.parameterValue == _dlc)

    def testREQ_ShallNotAcceptInvalidFlags(self):
        print
        _testValues = ["foo", -2, -1, 0, 2 ** 15, (2 ** 16) - 2,
          (2 ** 16) - 1, 2 ** 16, (2 ** 16) + 1]
        for _flags in _testValues:
            messageObject = None
            try:
                messageObject = CAN.Message(flags=_flags)
            except CAN.InvalidMessageParameterError as e:
                print e
            if isinstance(_flags, types.IntType) and \
               _flags in range(0, 2 ** 16):
                self.assert_(messageObject != None)
                self.assert_(messageObject.flags == _flags)
            else:
                self.assert_(messageObject == None)
                self.assert_(isinstance(e, CAN.InvalidMessageParameterError))
                self.assert_(e.parameterName == "flags")
                self.assert_(e.parameterValue == _flags)

    def testREQ_ShallProvideStringRepresentationOfCANMessage(self):
        print
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
        print
        stringRepresentations = []
        messages = []
        messages.append(CAN.InfoMessage())
        stringRepresentations.append("0.000000")
        messages.append(CAN.InfoMessage(timestamp=1.234567))
        stringRepresentations.append("1.234567")
        messages.append(CAN.InfoMessage(infoString="this is an info string"))
        stringRepresentations.append("0.000000\tthis is an info string")
        _infoString = "this is another info string"
        messages.append(CAN.InfoMessage(timestamp=2.345678,
                                        infoString=_infoString))
        stringRepresentations.append("2.345678\tthis is another info string")
        for _msg, _stringRep in zip(messages, stringRepresentations):
            self.assert_(_msg.__str__() == _stringRep)

if __name__ == "__main__":
    unittest.main()

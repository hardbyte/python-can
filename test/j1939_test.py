import unittest

try:
    import queue
except ImportError:
    import Queue as queue
import random


import can
can.rc['interface'] = 'socketcan_native'
from can.interfaces.interface import Bus

can_interface = 'vcan0'
from can.protocols import j1939

import logging
#logging.getLogger("").setLevel(logging.DEBUG)


def generate_long_messages(arbitration_id):
    for l in list(range(10)) + [100, 1000, 1784, 1785]:
        data = bytes([random.randrange(0, 2 ** 8 - 1) for b in range(l)])
        m = j1939.PDU(arbitration_id=arbitration_id, data=data)
        yield m, data


class J1939ImportTest(unittest.TestCase):

    def testProtocolImportable(self):
        assert hasattr(j1939, 'PDU')
        assert hasattr(j1939, 'ArbitrationID')


class StaticJ1939Test(unittest.TestCase):

    def setUp(self):
        self.arbitration_id = j1939.ArbitrationID()

    def assert_correct_message_data(self, m, data):
        self.assertEqual(len(m.data), len(data))
        assert all(d1 == d2 for d1, d2 in zip(m.data, data))

    def testCreateMessage(self):
        self.m = j1939.PDU(arbitration_id=self.arbitration_id)

    def testArbitrationIDEquality(self):
        self.testCreateMessage()
        self.assertEqual(self.m.arbitration_id, self.arbitration_id)

    def testMessageWithBytes(self):
        data_as_bytes = b'abc123'
        m = j1939.PDU(arbitration_id=self.arbitration_id, data=data_as_bytes)
        self.assert_correct_message_data(m, data_as_bytes)

    def testMessageWithByteArray(self):
        data_as_bytearray = bytearray(b'abc123')
        m = j1939.PDU(arbitration_id=self.arbitration_id, data=data_as_bytearray)
        self.assert_correct_message_data(m, data_as_bytearray)

    def testMessageWithList(self):
        data = [1, 4, 123, 35]
        m = j1939.PDU(arbitration_id=self.arbitration_id, data=data)
        self.assert_correct_message_data(m, data)

    def testLongMessage(self):
        # test message of length between 0 and 1785 bytes
        for m, data in generate_long_messages(self.arbitration_id):
            self.assert_correct_message_data(m, data)

    def testTooLongAMessage(self):
        data = bytes([random.randrange(0, 2 ** 8 - 1) for b in range(1786)])
        self.assertRaises(j1939.PDU, kwargs={'arbitration_id':self.arbitration_id, 'data':data})


class J1939BusTest(unittest.TestCase):
    def testCreateBus(self):
        self.bus = j1939.Bus(channel=can_interface)
        self.bus.shutdown()


class NetworkJ1939Test(unittest.TestCase):
    """

    """

    def setUp(self):
        super().setUp()
        self.bus = j1939.Bus(channel=can_interface)

    def tearDown(self):
        self.bus.shutdown()

    def testSendingJ1939Message(self):
        # this version puts the message through the network
        arbitration_id = j1939.ArbitrationID(pgn=65259)
        m = j1939.PDU(arbitration_id=arbitration_id, data=b'abc123')

        logging.debug("writing message: {}".format(m))
        self.bus.send(m)
        logging.debug("message written")

    def testSendingLongMessage(self):
        arbitration_id = j1939.ArbitrationID(pgn=0x22)
        for m, data in generate_long_messages(arbitration_id):
            self.bus.send(m)

    # TODO check that long messages are received

if __name__ == "__main__":
    unittest.main()

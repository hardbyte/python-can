from time import sleep
import unittest
import threading
from sys import version_info

try:
    import queue
except ImportError:
    import Queue as queue
import random


import can
from can.interfaces.interface import Bus

can_interface = 'vcan0'
from can.protocols import j1939

import logging
logging.getLogger("").setLevel(logging.DEBUG)


def generate_long_messages(arbitration_id):
    for l in list(range(10)) + [100, 1000, 1784, 1785]:
        data = bytearray([random.randrange(0, 2 ** 8 - 1) for b in range(l)])
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

    @unittest.skipIf(version_info < (3, 2), "bytes don't really exist in python 2")
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
        self.assertRaises(j1939.PDU, kwargs={'arbitration_id': self.arbitration_id, 'data': data})


class J1939BusTest(unittest.TestCase):

    def testCreateBus(self):
        self.bus = j1939.Bus(channel=can_interface)
        self.bus.shutdown()


class NetworkJ1939Test(unittest.TestCase):

    """

    """

    def setUp(self):
        super(NetworkJ1939Test, self).setUp()
        self.bus = j1939.Bus(channel=can_interface)

    def tearDown(self):
        sleep(0.2)
        self.bus.shutdown()

    def testSendingJ1939Message(self):
        # this version puts the message through the network
        arbitration_id = j1939.ArbitrationID(pgn=65259)
        m = j1939.PDU(arbitration_id=arbitration_id, data=bytearray(b'abc123'))

        logging.debug("writing message: {}".format(m))
        self.bus.send(m)
        logging.debug("message written")

    def _testSendingLongMessage(self):
        arbitration_id = j1939.ArbitrationID(pgn=0x22)

        for m, data in generate_long_messages(arbitration_id):
            sleep(0.050)
            self.bus.send(m)

    def testReceivingLongMessage(self):
        node = j1939.Node(self.bus, j1939.NodeName(0), [0x42, 0x01])

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        pgn = j1939.PGN(reserved_flag=True, pdu_specific=j1939.constants.DESTINATION_ADDRESS_GLOBAL)
        arbitration_id = j1939.ArbitrationID(pgn=pgn, source_address=0x01)
        m_out = j1939.PDU(arbitration_id=arbitration_id, data=data)

        otherbus = j1939.Bus(channel=can_interface)

        attempts = 0
        while attempts < 5:
            m_in = otherbus.recv(timeout=0.5)
            if m_in is not None:
                break
            # send a long message
            self.bus.send(m_out)
            attempts += 1

        self.assertIsNotNone(m_in, 'Should receive messages on can bus when sending long message')
        self.assertIsInstance(m_in, j1939.PDU)
        self.assertListEqual(m_in.data, m_out.data)

        otherbus.shutdown()


if __name__ == "__main__":
    unittest.main()

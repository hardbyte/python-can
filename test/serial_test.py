#!/usr/bin/env python

"""
This module is testing the serial interface.

Copyright: 2017 Boris Wenzlaff
"""

import unittest
from unittest.mock import patch

import can
from can.interfaces.serial.serial_can import SerialBus

from .config import IS_PYPY
from .message_helper import ComparingMessagesTestCase

# Mentioned in #1010
TIMEOUT = 0.5 if IS_PYPY else 0.1  # 0.1 is the default set in SerialBus


class SerialDummy:
    """
    Dummy to mock the serial communication
    """

    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1):
        return_value = bytearray()
        for i in range(size):
            return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg):
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None


class SimpleSerialTestBase(ComparingMessagesTestCase):
    MAX_TIMESTAMP = 0xFFFFFFFF / 1000

    def __init__(self):
        ComparingMessagesTestCase.__init__(
            self, allowed_timestamp_delta=None, preserves_channel=True
        )

    def test_can_protocol(self):
        self.assertEqual(self.bus.protocol, can.CanProtocol.CAN_20)

    def test_rx_tx_min_max_data(self):
        """
        Tests the transfer from 0x00 to 0xFF for a 1 byte payload
        """
        for b in range(0, 255):
            msg = can.Message(data=[b])
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertMessageEqual(msg, msg_receive)

    def test_rx_tx_min_max_dlc(self):
        """
        Tests the transfer from a 1 - 8 byte payload
        """
        payload = bytearray()
        for b in range(1, 9):
            payload.append(0)
            msg = can.Message(data=payload)
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertMessageEqual(msg, msg_receive)

    def test_rx_tx_data_none(self):
        """
        Tests the transfer without payload
        """
        msg = can.Message(data=None)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertMessageEqual(msg, msg_receive)

    def test_rx_tx_min_id(self):
        """
        Tests the transfer with the lowest arbitration id
        """
        msg = can.Message(arbitration_id=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertMessageEqual(msg, msg_receive)

    def test_rx_tx_max_id(self):
        """
        Tests the transfer with the highest arbitration id
        """
        msg = can.Message(arbitration_id=536870911)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertMessageEqual(msg, msg_receive)

    def test_rx_tx_max_timestamp(self):
        """
        Tests the transfer with the highest possible timestamp
        """

        msg = can.Message(timestamp=self.MAX_TIMESTAMP)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertMessageEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_max_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (max + 1)
        """
        msg = can.Message(timestamp=self.MAX_TIMESTAMP + 1)
        self.assertRaises(ValueError, self.bus.send, msg)

    def test_rx_tx_min_timestamp(self):
        """
        Tests the transfer with the lowest possible timestamp
        """
        msg = can.Message(timestamp=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertMessageEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_min_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (min - 1)
        """
        msg = can.Message(timestamp=-1)
        self.assertRaises(ValueError, self.bus.send, msg)

    def test_when_no_fileno(self):
        """
        Tests for the fileno method catching the missing pyserial implementeation on the Windows platform
        """
        try:
            fileno = self.bus.fileno()
        except NotImplementedError:
            pass  # allow it to be left non-implemented for Windows platform
        else:
            fileno.__gt__ = (
                lambda self, compare: True
            )  # Current platform implements fileno, so get the mock to respond to a greater than comparison
            self.assertIsNotNone(fileno)
            self.assertFalse(
                fileno == -1
            )  # forcing the value to -1 is the old way of managing fileno on Windows but it is not compatible with notifiers
            self.assertTrue(fileno > 0)


class SimpleSerialTest(unittest.TestCase, SimpleSerialTestBase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        SimpleSerialTestBase.__init__(self)

    def setUp(self):
        self.patcher = patch("serial.Serial")
        self.mock_serial = self.patcher.start()
        self.serial_dummy = SerialDummy()
        self.mock_serial.return_value.write = self.serial_dummy.write
        self.mock_serial.return_value.read = self.serial_dummy.read
        self.addCleanup(self.patcher.stop)
        self.bus = SerialBus("bus", timeout=TIMEOUT)

    def tearDown(self):
        self.serial_dummy.reset()


class SimpleSerialLoopTest(unittest.TestCase, SimpleSerialTestBase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        SimpleSerialTestBase.__init__(self)

    def setUp(self):
        self.bus = SerialBus("loop://", timeout=TIMEOUT)

    def tearDown(self):
        self.bus.shutdown()


if __name__ == "__main__":
    unittest.main()

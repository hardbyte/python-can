#!/usr/bin/env python
# coding: utf-8

"""
Name:        serial_test.py
Purpose:     Test of the simple serial interface

Copyright:   2017 - 2018 Boris Wenzlaff

This file is part of python-can <https://github.com/hardbyte/python-can/>.

python-can is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

python-can is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with python-can. If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
from mock import patch
from serial import SerialTimeoutException

import can
from can.interfaces.serial.serial_can import SerialBus


sleep_time_rx_tx = None


class SerialDummy:
    """
    Dummy to mock the serial communication
    """
    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1, timeout=0.1):
        return_value = bytearray()
        global sleep_time_rx_tx
        if self.msg is not None:
            if sleep_time_rx_tx is not None and timeout is not None:
                if sleep_time_rx_tx > timeout:
                    raise SerialTimeoutException()
            for i in range(size):
                return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg, timeout=0.1):
        global sleep_time_rx_tx
        if sleep_time_rx_tx is not None and timeout is not None:
            if sleep_time_rx_tx > timeout:
                raise SerialTimeoutException()
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None


class SimpleSerialTest(unittest.TestCase):
    MAX_TIMESTAMP = 0xFFFFFFFF / 1000

    def setUp(self):
        self.patcher = patch('serial.Serial')
        self.mock_serial = self.patcher.start()
        self.serial_dummy = SerialDummy()
        self.mock_serial.return_value.write = self.serial_dummy.write
        self.mock_serial.return_value.read = self.serial_dummy.read
        self.addCleanup(self.patcher.stop)
        self.bus = SerialBus('bus')
        global sleep_time_rx_tx
        sleep_time_rx_tx = None

    def tearDown(self):
        self.serial_dummy.reset()

    #@unittest.skip('skip, to speed up the other tests')
    def test_rx_tx_min_max_data(self):
        """
        Tests the transfer from 0x00 to 0xFF for a 1 byte payload
        """
        for b in range(0, 255):
            msg = can.Message(data=[b])
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertEqual(msg, msg_receive)

    #@unittest.skip('skip, to speed up the other tests')
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
            self.assertEqual(msg, msg_receive)

    def test_rx_tx_data_none(self):
        """
        Tests the transfer without payload
        """
        msg = can.Message(data=None)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_min_id(self):
        """
        Tests the transfer with the lowest arbitration id
        """
        msg = can.Message(arbitration_id=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_max_id(self):
        """
        Tests the transfer with the highest arbitration id
        """
        msg = can.Message(arbitration_id=536870911)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_max_timestamp(self):
        """
        Tests the transfer with the highest possible timestamp
        """

        msg = can.Message(timestamp=self.MAX_TIMESTAMP)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_max_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (max + 1)
        """
        msg = can.Message(timestamp=self.MAX_TIMESTAMP+1)
        self.assertRaises(ValueError, self.bus.send, msg)

    def test_rx_tx_min_timestamp(self):
        """
        Tests the transfer with the lowest possible timestamp
        """
        msg = can.Message(timestamp=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    def test_rx_tx_min_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (min - 1)
        """
        msg = can.Message(timestamp=-1)
        self.assertRaises(ValueError, self.bus.send, msg)

    def test_tx_timeout_default(self):
        """
        Tests for SerialTimeoutException for default timeout on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        with self.assertRaises(SerialTimeoutException):
            self.bus.send(can.Message(timestamp=1))

    def test_tx_non_timeout_default(self):
        """
        Tests for non SerialTimeoutException for default timeout on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.09
        self.bus.send(can.Message(timestamp=1))

    def test_tx_timeout_param(self):
        """
        Tests for SerialTimeoutException on send with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 3
        with self.assertRaises(SerialTimeoutException):
            self.bus.send(can.Message(timestamp=1), 2)

    def test_tx_non_timeout_param(self):
        """
        Tests for non SerialTimeoutException on send with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 1.9
        self.bus.send(can.Message(timestamp=1), 2)

    def test_tx_reset_timeout(self):
        """
        Tests reset of the timeout after a timeout is set with an parameter on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(can.Message(timestamp=1), 0.12)
        with self.assertRaises(SerialTimeoutException):
            self.bus.send(can.Message(timestamp=1))

    def test_rx_timeout_default(self):
        """
        Tests for SerialTimeoutException for default timeout on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(can.Message(timestamp=1), 100)
        with self.assertRaises(SerialTimeoutException):
            self.bus.recv()

    def test_rx_non_timeout_default(self):
        """
        Tests for non SerialTimeoutException for default timeout on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.09
        self.bus.send(can.Message(timestamp=1), 100)
        self.bus.recv()

    def test_rx_timeout_param(self):
        """
        Tests for SerialTimeoutException on receive with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 3
        self.bus.send(can.Message(timestamp=1), 100)
        with self.assertRaises(SerialTimeoutException):
            self.bus.recv(2)

    # TODO implement correctly
    @unittest.skip('skip, to speed up the other tests')
    def test_rx_non_timeout_param(self):
        """
        Tests for non SerialTimeoutException on receive with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 1.9
        self.bus.send(can.Message(timestamp=1), 2)

    # TODO implement correctly
    @unittest.skip('skip, to speed up the other tests')
    def test_rx_reset_timeout(self):
        """
        Tests reset of the timeout after a timeout is set with an parameter on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(can.Message(timestamp=1), 0.12)
        with self.assertRaises(SerialTimeoutException):
            self.bus.send(can.Message(timestamp=1))


if __name__ == '__main__':
    unittest.main()

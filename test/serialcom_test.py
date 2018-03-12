#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Name:        serialcom_test
Purpose:     ...

Author:      Boris Wenzlaff

Copyright:   2018 Boris Wenzlaff

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
from can.interfaces.serial.serialcom import SerialInterface
from can.message import Message

class SerialDummy:
    """
    Dummy to mock the serial communication
    """
    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1):
        return_value = bytearray()
        if size > len(self.msg):
            size = len(self.msg)
        for i in range(size):
            return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg):
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None


class SerialComTest(unittest.TestCase):
    TIMEOUT = 1

    def setUp(self):
        self.patcher = patch('serial.Serial')
        self.mock_serial = self.patcher.start()
        self.serial_dummy = SerialDummy()
        self.mock_serial.return_value.write = self.serial_dummy.write
        self.mock_serial.return_value.read = self.serial_dummy.read
        self.addCleanup(self.patcher.stop)
        self.serialcom = SerialInterface()

    def tearDown(self):
        self.serial_dummy.reset()

    def test_reset_timeout_send(self):
        """
        Tests the reset of the timeout after send over serial
        """
        serialcom = SerialInterface(timeout=self.TIMEOUT)
        serialcom.send_serial(msg=0x0, timeout=self.TIMEOUT + 5)
        self.assertEqual(self.TIMEOUT, serialcom.serial_timeout)

    def test_reset_timeout_receive(self):
        """
        Tests the reset of the timeout after receive over serial
        """
        serialcom = SerialInterface(timeout=self.TIMEOUT)
        serialcom.recv_serial(timeout=self.TIMEOUT + 5)
        self.assertEqual(self.TIMEOUT, serialcom.serial_timeout)

    def test_set_timeout(self):
        """
        Tests if the read and write are the same
        """
        # serialcom = SerialInterface(timeout=self.TIMEOUT)
        # self.assertEqual(serialcom.ser.timeout, serialcom.ser.write_timeout)


if __name__ == '__main__':
    unittest.main()

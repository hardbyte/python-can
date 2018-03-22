#!/usr/bin/env python
# coding: utf-8

"""
Name:        interface_simple_serial_test.py
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
import test.interface_test
from mock import patch
from serial import SerialTimeoutException
from can.interfaces.serial.simpleserial import SimpleSerialBus
from test.interface_test import GenericInterfaceTest


class SerialDummy:
    """
    Dummy to mock the serial communication
    """
    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1, timeout=0.1):
        return_value = bytearray()
        sleep = test.interface_test.sleep_time_rx_tx
        if self.msg is not None:
            if sleep is not None and timeout is not None:
                if sleep > timeout:
                    raise SerialTimeoutException()
            for i in range(size):
                return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg, timeout=0.1):
        sleep = test.interface_test.sleep_time_rx_tx
        if sleep is not None and timeout is not None:
            if sleep > timeout:
                raise SerialTimeoutException()
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None


class SimpleSerialTest(GenericInterfaceTest, unittest.TestCase):

    def setUp(self):
        # patch Serial
        self.patcher = patch('serial.Serial')
        self.mock_serial = self.patcher.start()
        self.serial_dummy = SerialDummy()
        self.mock_serial.return_value.write = self.serial_dummy.write
        self.mock_serial.return_value.read = self.serial_dummy.read
        self.addCleanup(self.patcher.stop)

        self.bus = SimpleSerialBus('bus')
        test.interface_test.sleep_time_rx_tx = None

    def tearDown(self):
        self.serial_dummy.reset()


if __name__ == '__main__':
    unittest.main()

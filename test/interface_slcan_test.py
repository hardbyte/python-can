#!/usr/bin/env python
# coding: utf-8

"""
Name:        interface_slcan_test.py
Purpose:     Test of the SLCAN interface

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
from can.interfaces.serial.slcan import SlcanBus
from test.interface_test import GenericInterfaceTest
from mock import patch


class SerialDummy:
    pass


class SerialRwPairDummy:
    pass


class SerialWrapperDummy:
    """
    Dummy to mock the serial wrapper communication
    """
    msg = None

    def __init__(self, *args, **kwargs):
        pass

    def readline(self):
        return self.msg

    def write(self, msg):
        self.msg = msg.replace('\r', '')

    def reset(self):
        self.msg = None


# TODO add documentation / how to for test implementation
# 1. create file
# 2. Mock underlying connections / devices -> send = recv
# 3. set timeout
# 4. add skip
class SlcanTest(GenericInterfaceTest, unittest.TestCase):

    def setUp(self):
        # patch TextIOWrapper
        self.patcher_wrapper = patch('io.TextIOWrapper')
        self.mock_wrapper = self.patcher_wrapper.start()
        self.wrapper_dummy = SerialWrapperDummy()
        self.mock_wrapper.return_value.write = self.wrapper_dummy.write
        self.mock_wrapper.return_value.readline = self.wrapper_dummy.readline
        self.addCleanup(self.patcher_wrapper.stop)

        # patch Serial
        self.patcher_serial = patch('serial.Serial')
        self.mock_serial = self.patcher_serial.start()
        self.serial_dummy = SerialDummy()
        self.addCleanup(self.patcher_serial.stop)

        # patch BufferedRWPair
        self.patcher_rwpair = patch('io.BufferedRWPair')
        self.mock_rwpair = self.patcher_rwpair.start()
        self.serial_rwpair = SerialRwPairDummy()
        self.addCleanup(self.patcher_rwpair.stop)

        self.bus = SlcanBus('bus')

    def tearDown(self):
        self.wrapper_dummy.reset()


if __name__ == '__main__':
    unittest.main()

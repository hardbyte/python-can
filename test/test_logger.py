#!/usr/bin/env python
# coding: utf-8

"""
This module tests the functions inside of logger.py
"""

import unittest
from unittest import mock
from unittest.mock import Mock
import sys
import can
import can.logger

from .config import *


class TestLoggerScriptModule(unittest.TestCase):
    def setUp(self) -> None:
        # Patch VirtualBus object
        patcher_virtual_bus = mock.patch("can.interfaces.virtual.VirtualBus", spec=True)
        self.MockVirtualBus = patcher_virtual_bus.start()
        self.addCleanup(patcher_virtual_bus.stop)
        self.mock_virtual_bus = self.MockVirtualBus.return_value
        self.mock_virtual_bus.shutdown = Mock()

        # Patch Logger object
        patcher_logger = mock.patch("can.logger.Logger", spec=True)
        self.MockLogger = patcher_logger.start()
        self.addCleanup(patcher_logger.stop)
        self.mock_logger = self.MockLogger.return_value
        self.mock_logger.stop = Mock()

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

    def assertSuccessfullCleanup(self):
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.shutdown.assert_called_once()

        self.MockLogger.assert_called_once()
        self.mock_logger.stop.assert_called_once()

    def test_log_virtual(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = [sys.argv[0], "-i", "virtual"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()

    def test_log_virtual_active(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = [sys.argv[0], "-i", "virtual", "--active"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()
        self.assertEqual(self.mock_virtual_bus.state, can.BusState.ACTIVE)

    def test_log_virtual_passive(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = [sys.argv[0], "-i", "virtual", "--passive"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()
        self.assertEqual(self.mock_virtual_bus.state, can.BusState.PASSIVE)


if __name__ == "__main__":
    unittest.main()

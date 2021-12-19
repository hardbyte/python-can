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
        patcher_logger = mock.patch("can.Logger", spec=True)
        self.MockLogger = patcher_logger.start()
        self.addCleanup(patcher_logger.stop)
        self.mock_logger = self.MockLogger.return_value
        self.mock_logger.stop = Mock()

        import can.logger as module

        self.module = module

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

    def test_log_virtual(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = [sys.argv[0], "-i", "virtual"]
        self.module.main()
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.shutdown.assert_called_once()

        self.MockLogger.assert_called_once()
        self.mock_logger.stop.assert_called_once()


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python

"""
This module tests the functions inside of logger.py
"""

import unittest
from unittest import mock
from unittest.mock import Mock
import gzip
import os
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

        self.MockLoggerUse = self.MockLogger
        self.loggerToUse = self.mock_logger

        # Patch SizedRotatingLogger object
        patcher_logger_sized = mock.patch("can.logger.SizedRotatingLogger", spec=True)
        self.MockLoggerSized = patcher_logger_sized.start()
        self.addCleanup(patcher_logger_sized.stop)
        self.mock_logger_sized = self.MockLoggerSized.return_value
        self.mock_logger_sized.stop = Mock()

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

        self.baseargs = [sys.argv[0], "-i", "virtual"]

    def assertSuccessfullCleanup(self):
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.shutdown.assert_called_once()

        self.MockLoggerUse.assert_called_once()
        self.loggerToUse.stop.assert_called_once()

    def test_log_virtual(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = self.baseargs
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()

    def test_log_virtual_active(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = self.baseargs + ["--active"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()
        self.assertEqual(self.mock_virtual_bus.state, can.BusState.ACTIVE)

    def test_log_virtual_passive(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = self.baseargs + ["--passive"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()
        self.assertEqual(self.mock_virtual_bus.state, can.BusState.PASSIVE)

    def test_log_virtual_with_config(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])

        sys.argv = self.baseargs + [
            "--bitrate",
            "250000",
            "--fd",
            "--data_bitrate",
            "2000000",
        ]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger.assert_called_once()

    def test_log_virtual_sizedlogger(self):
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])
        self.MockLoggerUse = self.MockLoggerSized
        self.loggerToUse = self.mock_logger_sized

        sys.argv = self.baseargs + ["--file_size", "1000000"]
        can.logger.main()
        self.assertSuccessfullCleanup()
        self.mock_logger_sized.assert_called_once()


class TestLoggerCompressedFile(unittest.TestCase):
    def setUp(self) -> None:
        # Patch VirtualBus object
        self.patcher_virtual_bus = mock.patch(
            "can.interfaces.virtual.VirtualBus", spec=True
        )
        self.MockVirtualBus = self.patcher_virtual_bus.start()
        self.mock_virtual_bus = self.MockVirtualBus.return_value

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )
        self.baseargs = [sys.argv[0], "-i", "virtual"]

        self.testfile = open("coffee.log.gz", "w+")

    def test_compressed_logfile(self):
        """
        Basic test to verify Logger is able to write gzip files.
        """
        self.mock_virtual_bus.recv = Mock(side_effect=[self.testmsg, KeyboardInterrupt])
        sys.argv = self.baseargs + ["--file_name", self.testfile.name]
        can.logger.main()
        with gzip.open(self.testfile.name, "rt") as testlog:
            last_line = testlog.readlines()[-1]

        self.assertEqual(last_line, "(0.000000) vcan0 00C0FFEE#0019000103010401\n")

    def tearDown(self) -> None:
        self.testfile.close()
        os.remove(self.testfile.name)
        self.patcher_virtual_bus.stop()


if __name__ == "__main__":
    unittest.main()

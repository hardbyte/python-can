#!/usr/bin/env python3
# coding: utf-8

"""
This module tests the functions inside of player.py
"""

import unittest
from unittest import mock
from unittest.mock import Mock
import os
import sys
import io
import can
import can.player


class TestPlayerScriptModule(unittest.TestCase):
    def setUp(self) -> None:
        # Patch VirtualBus object
        patcher_virtual_bus = mock.patch("can.interfaces.virtual.VirtualBus", spec=True)
        self.MockVirtualBus = patcher_virtual_bus.start()
        self.addCleanup(patcher_virtual_bus.stop)
        self.mock_virtual_bus = self.MockVirtualBus.return_value
        self.mock_virtual_bus.__enter__ = Mock(return_value=self.mock_virtual_bus)

        # Patch time sleep object
        patcher_sleep = mock.patch("can.io.player.sleep", spec=True)
        self.MockSleep = patcher_sleep.start()
        self.addCleanup(patcher_sleep.stop)

        self.baseargs = [sys.argv[0], "-i", "virtual"]
        self.logfile = os.path.join(
            os.path.dirname(__file__), "data", "test_CanMessage.asc"
        )

    def assertSuccessfulCleanup(self):
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.__exit__.assert_called_once()

    def test_play_virtual(self):
        sys.argv = self.baseargs + [self.logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 2)
        self.assertEqual(self.MockSleep.call_count, 2)
        self.assertSuccessfulCleanup()

    def test_play_virtual_verbose(self):
        sys.argv = self.baseargs + ["-v", self.logfile]
        with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            can.player.main()
        self.assertIn("09 08 07 06 05 04 03 02", mock_stdout.getvalue())
        self.assertIn("05 0c 00 00 00 00 00 00", mock_stdout.getvalue())
        self.assertEqual(self.mock_virtual_bus.send.call_count, 2)
        self.assertEqual(self.MockSleep.call_count, 2)
        self.assertSuccessfulCleanup()

    def test_play_virtual_exit(self):
        self.MockSleep.side_effect = [None, KeyboardInterrupt]

        sys.argv = self.baseargs + [self.logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 1)
        self.assertEqual(self.MockSleep.call_count, 2)
        self.assertSuccessfulCleanup()

    def test_play_skip_error_frame(self):
        logfile = os.path.join(
            os.path.dirname(__file__), "data", "logfile_errorframes.asc"
        )
        sys.argv = self.baseargs + ["-v", logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 9)
        self.assertEqual(self.MockSleep.call_count, 12)
        self.assertSuccessfulCleanup()

    def test_play_error_frame(self):
        logfile = os.path.join(
            os.path.dirname(__file__), "data", "logfile_errorframes.asc"
        )
        sys.argv = self.baseargs + ["-v", "--error-frames", logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 12)
        self.assertEqual(self.MockSleep.call_count, 12)
        self.assertSuccessfulCleanup()


if __name__ == "__main__":
    unittest.main()

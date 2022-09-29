#!/usr/bin/env python

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

    logfile = os.path.join(os.path.dirname(__file__), "data", "test_CanMessage.asc")

    def setUp(self) -> None:
        # Patch VirtualBus object
        patcher_virtual_bus = mock.patch("can.interfaces.virtual.VirtualBus", spec=True)
        self.MockVirtualBus = patcher_virtual_bus.start()
        self.addCleanup(patcher_virtual_bus.stop)
        self.mock_virtual_bus = self.MockVirtualBus.return_value
        self.mock_virtual_bus.__enter__ = Mock(return_value=self.mock_virtual_bus)

        # Patch time sleep object
        patcher_sleep = mock.patch("can.io.player.time.sleep", spec=True)
        self.MockSleep = patcher_sleep.start()
        self.addCleanup(patcher_sleep.stop)

        self.baseargs = [sys.argv[0], "-i", "virtual"]

    def assertSuccessfulCleanup(self):
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.__exit__.assert_called_once()

    def test_play_virtual(self):
        sys.argv = self.baseargs + [self.logfile]
        can.player.main()
        msg1 = can.Message(
            timestamp=2.501,
            arbitration_id=0xC8,
            is_extended_id=False,
            is_fd=False,
            is_rx=False,
            channel=1,
            dlc=8,
            data=[0x9, 0x8, 0x7, 0x6, 0x5, 0x4, 0x3, 0x2],
        )
        msg2 = can.Message(
            timestamp=17.876708,
            arbitration_id=0x6F9,
            is_extended_id=False,
            is_fd=False,
            is_rx=True,
            channel=0,
            dlc=8,
            data=[0x5, 0xC, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
        )
        if sys.version_info >= (3, 8):
            # The args argument was introduced with python 3.8
            self.assertTrue(
                msg1.equals(self.mock_virtual_bus.send.mock_calls[0].args[0])
            )
            self.assertTrue(
                msg2.equals(self.mock_virtual_bus.send.mock_calls[1].args[0])
            )
        self.assertSuccessfulCleanup()

    def test_play_virtual_verbose(self):
        sys.argv = self.baseargs + ["-v", self.logfile]
        with unittest.mock.patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            can.player.main()
        self.assertIn("09 08 07 06 05 04 03 02", mock_stdout.getvalue())
        self.assertIn("05 0c 00 00 00 00 00 00", mock_stdout.getvalue())
        self.assertEqual(self.mock_virtual_bus.send.call_count, 2)
        self.assertSuccessfulCleanup()

    def test_play_virtual_exit(self):
        self.MockSleep.side_effect = [None, KeyboardInterrupt]

        sys.argv = self.baseargs + [self.logfile]
        can.player.main()
        assert self.mock_virtual_bus.send.call_count <= 2
        self.assertSuccessfulCleanup()

    def test_play_skip_error_frame(self):
        logfile = os.path.join(
            os.path.dirname(__file__), "data", "logfile_errorframes.asc"
        )
        sys.argv = self.baseargs + ["-v", logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 9)
        self.assertSuccessfulCleanup()

    def test_play_error_frame(self):
        logfile = os.path.join(
            os.path.dirname(__file__), "data", "logfile_errorframes.asc"
        )
        sys.argv = self.baseargs + ["-v", "--error-frames", logfile]
        can.player.main()
        self.assertEqual(self.mock_virtual_bus.send.call_count, 12)
        self.assertSuccessfulCleanup()


class TestPlayerCompressedFile(TestPlayerScriptModule):
    """
    Re-run tests using a compressed file.
    """

    logfile = os.path.join(os.path.dirname(__file__), "data", "test_CanMessage.asc.gz")


if __name__ == "__main__":
    unittest.main()

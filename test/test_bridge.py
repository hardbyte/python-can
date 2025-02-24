#!/usr/bin/env python

"""
This module tests the functions inside of bridge.py
"""

import sys
import unittest
from unittest import mock
from unittest.mock import Mock

import can
import can.bridge


class TestBridgeScriptModule(unittest.TestCase):
    def setUp(self) -> None:
        # Patch VirtualBus object
        patcher_virtual_bus = mock.patch("can.interfaces.virtual.VirtualBus", spec=True)
        self.MockVirtualBus = patcher_virtual_bus.start()
        self.addCleanup(patcher_virtual_bus.stop)
        self.mock_virtual_bus = self.MockVirtualBus.return_value
        self.mock_virtual_bus.__enter__ = Mock(return_value=self.mock_virtual_bus)

        # Patch time sleep object
        patcher_sleep = mock.patch("can.bridge.time.sleep", spec=True)
        self.MockSleep = patcher_sleep.start()
        self.addCleanup(patcher_sleep.stop)

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

        self.busargs = ["-i", "virtual"]

    def assert_successfull_cleanup(self):
        self.MockVirtualBus.assert_called()
        self.assertEqual(2, len(self.mock_virtual_bus.__exit__.mock_calls))

    def test_bridge_no_config(self):
        self.MockSleep.side_effect = KeyboardInterrupt
        sys.argv = [
            sys.argv[0],
            *self.busargs,
            "-c",
            "can_a",
            "--",
            *self.busargs,
            "-c",
            "can_b",
        ]
        #can.bridge.main()

        #self.assert_successfull_cleanup()


if __name__ == "__main__":
    unittest.main()

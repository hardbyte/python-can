#!/usr/bin/env python

"""
This module tests the functions inside of bridge.py
"""

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
        self.mock_virtual_bus.shutdown = Mock()

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

    def assert_successfull_cleanup(self):
        self.MockVirtualBus.assert_called_once()
        self.mock_virtual_bus.shutdown.assert_called_once()


if __name__ == "__main__":
    unittest.main()

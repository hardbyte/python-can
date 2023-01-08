#!/usr/bin/env python

"""
This module tests sending messages on socketcan with and without local_loopback flag

for a good explanation of why this might be needed:
https://www.kernel.org/doc/html/v4.17/networking/can.html#socketcan-local-loopback1
"""
import unittest

import can

from .config import TEST_INTERFACE_SOCKETCAN


@unittest.skipUnless(TEST_INTERFACE_SOCKETCAN, "skip testing of socketcan")
class LocalLoopbackSocketCan(unittest.TestCase):
    """test local_loopback functionality"""

    BITRATE = 500000
    TIMEOUT = 0.1

    INTERFACE_1 = "socketcan"
    CHANNEL_1 = "vcan0"
    INTERFACE_2 = "socketcan"
    CHANNEL_2 = "vcan0"

    def setUp(self):
        self._recv_bus = can.Bus(
            interface=self.INTERFACE_2, channel=self.CHANNEL_2, bitrate=self.BITRATE
        )

    def tearDown(self):
        self._recv_bus.shutdown()

    def test_sending_message_with_loopback_enabled(self):
        """test that sending messages with local_loopback=True produces output even
        on the local device"""
        loopback_send_bus = can.Bus(
            interface=self.INTERFACE_1,
            channel=self.CHANNEL_1,
            bitrate=self.BITRATE,
            local_loopback=True,
        )
        try:
            msg = can.Message(arbitration_id=0x123, is_extended_id=False)
            loopback_send_bus.send(msg)
            recv_msg = self._recv_bus.recv(self.TIMEOUT)
            self.assertIsNotNone(recv_msg)
            recv_msg_lb = loopback_send_bus.recv(self.TIMEOUT)
            self.assertIsNone(recv_msg_lb)
        finally:
            loopback_send_bus.shutdown()

    def test_sending_message_without_loopback_enabled(self):
        """test that sending messages with local_loopback=False does not produce output
        on the local device"""
        noloopback_send_bus = can.Bus(
            interface=self.INTERFACE_1,
            channel=self.CHANNEL_1,
            bitrate=self.BITRATE,
            local_loopback=False,
        )
        try:
            msg = can.Message(arbitration_id=0x123, is_extended_id=False)
            noloopback_send_bus.send(msg)
            recv_msg = self._recv_bus.recv(self.TIMEOUT)
            self.assertIsNone(recv_msg)
            recv_msg_nlb = noloopback_send_bus.recv(self.TIMEOUT)
            self.assertIsNone(recv_msg_nlb)
        finally:
            noloopback_send_bus.shutdown()


if __name__ == "__main__":
    unittest.main()

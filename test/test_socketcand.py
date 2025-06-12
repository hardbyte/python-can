#!/usr/bin/env python

import unittest
import can
from can.interfaces.socketcand import socketcand


class TestConvertAsciiMessageToCanMessage(unittest.TestCase):
    def test_valid_frame_message(self):
        # Example: < frame 123 1680000000.0 01020304 >
        ascii_msg = "< frame 123 1680000000.0 01020304 >"
        msg = socketcand.convert_ascii_message_to_can_message(ascii_msg)
        self.assertIsInstance(msg, can.Message)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.timestamp, 1680000000.0)
        self.assertEqual(msg.data, bytearray([1, 2, 3, 4]))
        self.assertEqual(msg.dlc, 4)
        self.assertFalse(msg.is_extended_id)
        self.assertTrue(msg.is_rx)

    def test_valid_error_message(self):
        # Example: < error 1ABCDEF0 1680000001.0 >
        ascii_msg = "< error 1ABCDEF0 1680000001.0 >"
        msg = socketcand.convert_ascii_message_to_can_message(ascii_msg)
        self.assertIsInstance(msg, can.Message)
        self.assertEqual(msg.arbitration_id, 0x1ABCDEF0)
        self.assertEqual(msg.timestamp, 1680000001.0)
        self.assertEqual(msg.data, bytearray([0]))
        self.assertEqual(msg.dlc, 1)
        self.assertTrue(msg.is_extended_id)
        self.assertTrue(msg.is_error_frame)
        self.assertTrue(msg.is_rx)

    def test_invalid_message(self):
        ascii_msg = "< unknown 123 0.0 >"
        msg = socketcand.convert_ascii_message_to_can_message(ascii_msg)
        self.assertIsNone(msg)

    def test_missing_ending_character(self):
        ascii_msg = "< frame 123 1680000000.0 01020304"
        msg = socketcand.convert_ascii_message_to_can_message(ascii_msg)
        self.assertIsNone(msg)


if __name__ == "__main__":
    unittest.main()

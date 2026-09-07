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


class TestConvertCanMessageToAsciiMessage(unittest.TestCase):
    def test_standard_frame(self):
        msg = can.Message(
            arbitration_id=0x123, data=[0x01, 0x02, 0x03, 0x04], is_extended_id=False
        )
        self.assertEqual(
            socketcand.convert_can_message_to_ascii_message(msg),
            "< send 123 4 1 2 3 4 >",
        )

    def test_extended_frame(self):
        msg = can.Message(
            arbitration_id=0x1AAAAAAA, data=[0x01, 0xF1], is_extended_id=True
        )
        self.assertEqual(
            socketcand.convert_can_message_to_ascii_message(msg),
            "< send 1AAAAAAA 2 1 f1 >",
        )

    def test_remote_frame_is_refused(self):
        msg = can.Message(
            arbitration_id=0x403, is_remote_frame=True, is_extended_id=False
        )
        with self.assertRaises(can.CanOperationError):
            socketcand.convert_can_message_to_ascii_message(msg)


if __name__ == "__main__":
    unittest.main()

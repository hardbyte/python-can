#!/usr/bin/env python

import socket
import threading
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


class TestHandshake(unittest.TestCase):
    """The server replies arrive on a TCP stream, so a read can hold part
    of a reply or a reply followed by frames."""

    def _serve(self, chunks):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        self.addCleanup(server.close)

        def run():
            conn, _ = server.accept()
            with conn:
                for expected_cmd, reply_chunks in chunks:
                    if expected_cmd:
                        received = b""
                        while not received.endswith(b">"):
                            received += conn.recv(256)
                        self.assertEqual(received.decode("ascii"), expected_cmd)
                    for chunk in reply_chunks:
                        conn.sendall(chunk.encode("ascii"))
                        threading.Event().wait(0.05)
                # wait for the client to close the connection
                while conn.recv(256):
                    pass

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        self.addCleanup(thread.join, 2)
        return server.getsockname()[1]

    def test_frames_in_same_read_as_rawmode_ok(self):
        port = self._serve(
            [
                (None, ["< hi >"]),
                ("< open can0 >", ["< ok >"]),
                ("< rawmode >", ["< ok >< frame 123 1680000000.0 0102 >"]),
            ]
        )
        with can.Bus(
            interface="socketcand", channel="can0", host="127.0.0.1", port=port
        ) as bus:
            msg = bus.recv(timeout=1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.data, bytearray([1, 2]))
        self.assertEqual(msg.channel, "can0")

    def test_reply_split_over_reads(self):
        port = self._serve(
            [
                (None, ["< h", "i >"]),
                ("< open can0 >", ["< o", "k >"]),
                ("< rawmode >", ["< ok >"]),
            ]
        )
        with can.Bus(
            interface="socketcand", channel="can0", host="127.0.0.1", port=port
        ) as bus:
            self.assertIsNone(bus.recv(timeout=0.1))

    def test_unexpected_reply_raises(self):
        port = self._serve(
            [
                (None, ["< hi >"]),
                ("< open can0 >", ["< error could not open bus >"]),
            ]
        )
        with self.assertRaises(can.CanError):
            can.Bus(interface="socketcand", channel="can0", host="127.0.0.1", port=port)


if __name__ == "__main__":
    unittest.main()

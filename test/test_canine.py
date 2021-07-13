#!/usr/bin/env python
# coding: utf-8

import unittest
import can
import struct
from unittest.mock import Mock


class canineTestCase(unittest.TestCase):
    def setUp(self):
        self.bus = can.Bus("loop://", bustype="canine", usb_dev=MockUSB())
        self.dev = self.bus.dev
        self.dev.read(0x81, 64)

    def tearDown(self):
        self.bus.shutdown()

    def test_encode(self):
        packed = struct.pack('>L', 0x12ABCDEF)
        self.assertTrue(packed, b'\x12\xab\xcd\xef')

    def test_recv_extended(self):
        self.dev.write(0x1, b"\x00T\x12\xab\xcd\xef\x02\xAA\x55")
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

    def test_send_extended(self):
        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, data=[0xAA, 0x55]
        )
        self.bus.send(msg)
        data = self.dev.read(0x81, 64)
        self.assertEqual(data, b'\x00T\x12\xab\xcd\xef\x02\xaaU')

    def test_recv_standard(self):
        self.dev.write(0x1, b"\x00t\x04\x56\x03\x11\x22\x33")
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x456)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 3)
        self.assertSequenceEqual(msg.data, [0x11, 0x22, 0x33])

    def test_send_standard(self):
        msg = can.Message(
            arbitration_id=0x456, is_extended_id=False, data=[0x11, 0x22, 0x33]
        )
        self.bus.send(msg)
        data = self.dev.read(0x81, 64)
        self.assertEqual(data, b'\x00t\x04\x56\x03\x11\x22\x33')

    def test_recv_standard_remote(self):
        self.dev.write(0x1, b"\x00r\x01\x23\x08")
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 8)

    def test_send_standard_remote(self):
        msg = can.Message(
            arbitration_id=0x123, is_extended_id=False, is_remote_frame=True, dlc=8
        )
        self.bus.send(msg)
        data = self.dev.read(0x81, 64)
        self.assertEqual(data, b"\x00r\x01\x23\x08")

    def test_recv_extended_remote(self):
        self.dev.write(0x1, b"\x00R\x12\xab\xcd\xef\x06")
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 6)

    def test_send_extended_remote(self):
        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, is_remote_frame=True, dlc=6
        )
        self.bus.send(msg)
        data = self.dev.read(0x81, 64)
        self.assertEqual(data, b"\x00R\x12\xab\xcd\xef\x06")

    def test_version(self):
        self.dev.write(0x1, b"\x00V\x00\x0A\x00\x0D")
        self.dev.freeze()
        hw_ver, sw_ver = self.bus.get_version(0)
        self.assertEqual(hw_ver, 10)
        self.assertEqual(sw_ver, 13)
        self.dev.unfreeze()
        

class MockUSB:

    def __init__(self):
        self.val = None
        self._ctx = Mock()
        self._frozen = False

    def write(self, ep, val):
        if not self._frozen:
            self.val = val

    def read(self, ep, length):
        return self.val

    def set_configuration(self):
        pass

    def freeze(self):
        self._frozen = True

    def unfreeze(self):
        self._frozen = False


if __name__ == "__main__":
    unittest.main()

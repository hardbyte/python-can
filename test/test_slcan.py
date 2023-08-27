#!/usr/bin/env python

import unittest
from typing import cast

import serial

import can

from .config import IS_PYPY

"""
Mentioned in #1010 & #1490

> PyPy works best with pure Python applications. Whenever you use a C extension module,
> it runs much slower than in CPython. The reason is that PyPy can't optimize C extension modules since they're not fully supported.
> In addition, PyPy has to emulate reference counting for that part of the code, making it even slower.

https://realpython.com/pypy-faster-python/#it-doesnt-work-well-with-c-extensions
"""
TIMEOUT = 0.5 if IS_PYPY else 0.01  # 0.001 is the default set in slcanBus


class slcanTestCase(unittest.TestCase):
    def setUp(self):
        self.bus = cast(
            can.interfaces.slcan.slcanBus,
            can.Bus("loop://", interface="slcan", sleep_after_open=0, timeout=TIMEOUT),
        )
        self.serial = cast(serial.Serial, self.bus.serialPortOrig)
        self.serial.reset_input_buffer()

    def tearDown(self):
        self.bus.shutdown()

    def test_recv_extended(self):
        self.serial.write(b"T12ABCDEF2AA55\r")
        msg = self.bus.recv(TIMEOUT)
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
        expected = b"T12ABCDEF2AA55\r"
        data = self.serial.read(len(expected))
        self.assertEqual(data, expected)

    def test_recv_standard(self):
        self.serial.write(b"t4563112233\r")
        msg = self.bus.recv(TIMEOUT)
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
        expected = b"t4563112233\r"
        data = self.serial.read(len(expected))
        self.assertEqual(data, expected)

    def test_recv_standard_remote(self):
        self.serial.write(b"r1238\r")
        msg = self.bus.recv(TIMEOUT)
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
        expected = b"r1238\r"
        data = self.serial.read(len(expected))
        self.assertEqual(data, expected)

    def test_recv_extended_remote(self):
        self.serial.write(b"R12ABCDEF6\r")
        msg = self.bus.recv(TIMEOUT)
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
        expected = b"R12ABCDEF6\r"
        data = self.serial.read(len(expected))
        self.assertEqual(data, expected)

    def test_partial_recv(self):
        self.serial.write(b"T12ABCDEF")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNone(msg)

        self.serial.write(b"2AA55\rT12")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

        msg = self.bus.recv(TIMEOUT)
        self.assertIsNone(msg)

        self.serial.write(b"ABCDEF2AA55\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)

    def test_version(self):
        self.serial.write(b"V1013\r")
        hw_ver, sw_ver = self.bus.get_version(0)
        self.assertEqual(hw_ver, 10)
        self.assertEqual(sw_ver, 13)

        hw_ver, sw_ver = self.bus.get_version(0)
        self.assertIsNone(hw_ver)
        self.assertIsNone(sw_ver)

    def test_serial_number(self):
        self.serial.write(b"NA123\r")
        sn = self.bus.get_serial_number(0)
        self.assertEqual(sn, "A123")

        sn = self.bus.get_serial_number(0)
        self.assertIsNone(sn)


if __name__ == "__main__":
    unittest.main()

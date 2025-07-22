#!/usr/bin/env python

import unittest.mock
from typing import cast, Optional

from serial.serialutil import SerialBase

import can.interfaces.slcan

from .config import IS_PYPY

"""
Mentioned in #1010 & #1490

> PyPy works best with pure Python applications. Whenever you use a C extension module,
> it runs much slower than in CPython. The reason is that PyPy can't optimize C extension modules since they're not fully supported.
> In addition, PyPy has to emulate reference counting for that part of the code, making it even slower.

https://realpython.com/pypy-faster-python/#it-doesnt-work-well-with-c-extensions
"""
TIMEOUT = 0.5 if IS_PYPY else 0.01  # 0.001 is the default set in slcanBus


class SerialMock(SerialBase):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._input_buffer = b""
        self._output_buffer = b""

    def open(self) -> None:
        self.is_open = True

    def close(self) -> None:
        self.is_open = False
        self._input_buffer = b""
        self._output_buffer = b""

    def read(self, size: int = -1, /) -> bytes:
        if size > 0:
            data = self._input_buffer[:size]
            self._input_buffer = self._input_buffer[size:]
            return data
        return b""

    def write(self, b: bytes, /) -> Optional[int]:
        self._output_buffer = b
        if b == b"N\r":
            self.set_input_buffer(b"NA123\r")
        elif b == b"V\r":
            self.set_input_buffer(b"V1013\r")
        return len(b)

    def set_input_buffer(self, expected: bytes) -> None:
        self._input_buffer = expected

    def get_output_buffer(self) -> bytes:
        return self._output_buffer

    def reset_input_buffer(self) -> None:
        self._input_buffer = b""

    @property
    def in_waiting(self) -> int:
        return len(self._input_buffer)

    @classmethod
    def serial_for_url(cls, *args, **kwargs) -> SerialBase:
        return cls(*args, **kwargs)


class slcanTestCase(unittest.TestCase):
    @unittest.mock.patch("serial.serial_for_url", SerialMock.serial_for_url)
    def setUp(self):
        self.bus = cast(
            can.interfaces.slcan.slcanBus,
            can.Bus("loop://", interface="slcan", sleep_after_open=0, timeout=TIMEOUT),
        )
        self.serial = cast(SerialMock, self.bus.serialPortOrig)
        self.serial.reset_input_buffer()

    def tearDown(self):
        self.bus.shutdown()

    def test_recv_extended(self):
        self.serial.set_input_buffer(b"T12ABCDEF2AA55\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

        # Ewert Energy Systems CANDapter specific
        self.serial.set_input_buffer(b"x12ABCDEF2AA55\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

    def test_send_extended(self):
        payload = b"T12ABCDEF2AA55\r"
        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, data=[0xAA, 0x55]
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_standard(self):
        self.serial.set_input_buffer(b"t4563112233\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x456)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 3)
        self.assertSequenceEqual(msg.data, [0x11, 0x22, 0x33])

    def test_send_standard(self):
        payload = b"t4563112233\r"
        msg = can.Message(
            arbitration_id=0x456, is_extended_id=False, data=[0x11, 0x22, 0x33]
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_standard_remote(self):
        self.serial.set_input_buffer(b"r1238\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 8)

    def test_send_standard_remote(self):
        payload = b"r1238\r"
        msg = can.Message(
            arbitration_id=0x123, is_extended_id=False, is_remote_frame=True, dlc=8
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_extended_remote(self):
        self.serial.set_input_buffer(b"R12ABCDEF6\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 6)

    def test_send_extended_remote(self):
        payload = b"R12ABCDEF6\r"
        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, is_remote_frame=True, dlc=6
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_fd(self):
        self.serial.set_input_buffer(b"d123A303132333435363738393a3b3c3d3e3f\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.is_fd, True)
        self.assertEqual(msg.bitrate_switch, False)
        self.assertEqual(msg.dlc, 16)
        self.assertSequenceEqual(
            msg.data,
            [
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )

    def test_send_fd(self):
        payload = b"d123A303132333435363738393A3B3C3D3E3F\r"
        msg = can.Message(
            arbitration_id=0x123,
            is_extended_id=False,
            is_fd=True,
            data=[
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_fd_extended(self):
        self.serial.set_input_buffer(b"D12ABCDEFA303132333435363738393A3B3C3D3E3F\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 16)
        self.assertEqual(msg.bitrate_switch, False)
        self.assertTrue(msg.is_fd)
        self.assertSequenceEqual(
            msg.data,
            [
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )

    def test_send_fd_extended(self):
        payload = b"D12ABCDEFA303132333435363738393A3B3C3D3E3F\r"
        msg = can.Message(
            arbitration_id=0x12ABCDEF,
            is_extended_id=True,
            is_fd=True,
            data=[
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_fd_brs(self):
        self.serial.set_input_buffer(b"b123A303132333435363738393a3b3c3d3e3f\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.is_fd, True)
        self.assertEqual(msg.bitrate_switch, True)
        self.assertEqual(msg.dlc, 16)
        self.assertSequenceEqual(
            msg.data,
            [
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )

    def test_send_fd_brs(self):
        payload = b"b123A303132333435363738393A3B3C3D3E3F\r"
        msg = can.Message(
            arbitration_id=0x123,
            is_extended_id=False,
            is_fd=True,
            bitrate_switch=True,
            data=[
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_recv_fd_brs_extended(self):
        self.serial.set_input_buffer(b"B12ABCDEFA303132333435363738393A3B3C3D3E3F\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 16)
        self.assertEqual(msg.bitrate_switch, True)
        self.assertTrue(msg.is_fd)
        self.assertSequenceEqual(
            msg.data,
            [
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )

    def test_send_fd_brs_extended(self):
        payload = b"B12ABCDEFA303132333435363738393A3B3C3D3E3F\r"
        msg = can.Message(
            arbitration_id=0x12ABCDEF,
            is_extended_id=True,
            is_fd=True,
            bitrate_switch=True,
            data=[
                0x30,
                0x31,
                0x32,
                0x33,
                0x34,
                0x35,
                0x36,
                0x37,
                0x38,
                0x39,
                0x3A,
                0x3B,
                0x3C,
                0x3D,
                0x3E,
                0x3F,
            ],
        )
        self.bus.send(msg)
        self.assertEqual(payload, self.serial.get_output_buffer())

        self.serial.set_input_buffer(payload)
        rx_msg = self.bus.recv(TIMEOUT)
        self.assertTrue(msg.equals(rx_msg, timestamp_delta=None))

    def test_partial_recv(self):
        self.serial.set_input_buffer(b"T12ABCDEF")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNone(msg)

        self.serial.set_input_buffer(b"2AA55\rT12")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

        msg = self.bus.recv(TIMEOUT)
        self.assertIsNone(msg)

        self.serial.set_input_buffer(b"ABCDEF2AA55\r")
        msg = self.bus.recv(TIMEOUT)
        self.assertIsNotNone(msg)

    def test_version(self):
        hw_ver, sw_ver = self.bus.get_version(0)
        self.assertEqual(b"V\r", self.serial.get_output_buffer())
        self.assertEqual(hw_ver, 10)
        self.assertEqual(sw_ver, 13)

    def test_serial_number(self):
        sn = self.bus.get_serial_number(0)
        self.assertEqual(b"N\r", self.serial.get_output_buffer())
        self.assertEqual(sn, "A123")


if __name__ == "__main__":
    unittest.main()

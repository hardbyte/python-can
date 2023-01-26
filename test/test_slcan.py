#!/usr/bin/env python

import os
import threading
import time
import unittest
from platform import platform

import pytest

import can


class slcanTestCase(unittest.TestCase):
    def setUp(self):
        self.bus = can.Bus("loop://", interface="slcan", sleep_after_open=0)
        self.serial = self.bus.serialPortOrig
        self.serial.read(self.serial.in_waiting)

    def tearDown(self):
        self.bus.shutdown()

    def test_recv_extended(self):
        self.serial.write(b"T12ABCDEF2AA55\r")
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
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b"T12ABCDEF2AA55\r")

    def test_recv_standard(self):
        self.serial.write(b"t4563112233\r")
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
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b"t4563112233\r")

    def test_recv_standard_remote(self):
        self.serial.write(b"r1238\r")
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
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b"r1238\r")

    def test_recv_extended_remote(self):
        self.serial.write(b"R12ABCDEF6\r")
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
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b"R12ABCDEF6\r")

    def test_partial_recv(self):
        self.serial.write(b"T12ABCDEF")
        msg = self.bus.recv(0)
        self.assertIsNone(msg)

        self.serial.write(b"2AA55\rT12")
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

        msg = self.bus.recv(0)
        self.assertIsNone(msg)

        self.serial.write(b"ABCDEF2AA55\r")
        msg = self.bus.recv(0)
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


@pytest.fixture
def pseudo_terminal():
    import pty

    main, peripheral = pty.openpty()

    return main, peripheral


@pytest.fixture
def bus(pseudo_terminal):
    _, peripheral = pseudo_terminal
    return can.Bus(os.ttyname(peripheral), interface="slcan", sleep_after_open=0)


@pytest.fixture
def bus_writer(pseudo_terminal):
    main, _ = pseudo_terminal
    writer = os.fdopen(main, "wb")
    return writer


@pytest.mark.skipif("linux" not in platform().lower(), reason="Requires Linux")
@pytest.mark.parametrize("timeout", [0.5, 1])
def test_verify_recv_timeout(timeout, bus, bus_writer):
    msg = b"Hello"
    unterminated = msg
    terminated = msg + b"\r"

    def consecutive_writes():
        bus_writer.write(terminated)
        bus_writer.flush()
        time.sleep(timeout / 2)
        bus_writer.write(unterminated)
        bus_writer.flush()

    timeout_ms = int(timeout * 1_000)
    allowable_timeout_error = timeout_ms / 200

    writer_thread = threading.Thread(target=consecutive_writes)

    start_time = time.time_ns()
    writer_thread.start()
    bus.recv(timeout)
    stop_time = time.time_ns()

    duration_ms = int((stop_time - start_time) / 1_000_000)
    assert duration_ms - timeout_ms < allowable_timeout_error


if __name__ == "__main__":
    unittest.main()

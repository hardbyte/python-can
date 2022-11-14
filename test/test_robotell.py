#!/usr/bin/env python

import unittest
import can


class robotellTestCase(unittest.TestCase):
    def setUp(self):
        # will log timeout messages since we are not feeding ack messages to the serial port at this stage
        self.bus = can.Bus("loop://", bustype="robotell")
        self.serial = self.bus.serialPortOrig
        self.serial.read(self.serial.in_waiting)

    def tearDown(self):
        self.bus.shutdown()

    def test_recv_extended(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x56,
                    0x34,
                    0x12,
                    0x00,
                    0xA5,
                    0xAA,
                    0xA5,
                    0xA5,
                    0xA5,
                    0x55,
                    0xA5,
                    0x55,
                    0xA5,
                    0xA5,
                    0xA5,
                    0xAA,
                    0x00,
                    0x00,
                    0x06,
                    0x00,
                    0x01,
                    0x00,
                    0xEB,
                    0x55,
                    0x55,
                ]
            )
        )
        msg = self.bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123456)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 6)
        self.assertSequenceEqual(msg.data, [0xAA, 0xA5, 0x55, 0x55, 0xA5, 0xAA])
        data = self.serial.read(self.serial.in_waiting)

    def test_send_extended(self):
        msg = can.Message(
            arbitration_id=0x123456,
            is_extended_id=True,
            data=[0xAA, 0xA5, 0x55, 0x55, 0xA5, 0xAA],
        )
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x56,
                    0x34,
                    0x12,
                    0x00,
                    0xA5,
                    0xAA,
                    0xA5,
                    0xA5,
                    0xA5,
                    0x55,
                    0xA5,
                    0x55,
                    0xA5,
                    0xA5,
                    0xA5,
                    0xAA,
                    0x00,
                    0x00,
                    0x06,
                    0x00,
                    0x01,
                    0x00,
                    0xEB,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_recv_standard(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x7B,
                    0x00,
                    0x00,
                    0x00,
                    0x48,
                    0x65,
                    0x6C,
                    0x6C,
                    0x6F,
                    0x31,
                    0x32,
                    0x33,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x0D,
                    0x55,
                    0x55,
                ]
            )
        )
        msg = self.bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 8)
        self.assertSequenceEqual(
            msg.data, [0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x31, 0x32, 0x33]
        )
        data = self.serial.read(self.serial.in_waiting)

    def test_send_standard(self):
        msg = can.Message(
            arbitration_id=123,
            is_extended_id=False,
            data=[0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x31, 0x32, 0x33],
        )
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x7B,
                    0x00,
                    0x00,
                    0x00,
                    0x48,
                    0x65,
                    0x6C,
                    0x6C,
                    0x6F,
                    0x31,
                    0x32,
                    0x33,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x0D,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_recv_extended_remote(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x56,
                    0x34,
                    0x12,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x07,
                    0x00,
                    0x01,
                    0x01,
                    0xA5,
                    0xA5,
                    0x55,
                    0x55,
                ]
            )
        )
        msg = self.bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123456)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 7)
        data = self.serial.read(self.serial.in_waiting)

    def test_send_extended_remote(self):
        msg = can.Message(
            arbitration_id=0x123456, is_extended_id=True, is_remote_frame=True, dlc=7
        )
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x56,
                    0x34,
                    0x12,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x07,
                    0x00,
                    0x01,
                    0x01,
                    0xA5,
                    0xA5,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_partial_recv(self):
        # write some junk data and then start of message
        self.serial.write(
            bytearray([0x11, 0x22, 0x33, 0xAA, 0xAA, 0x7B, 0x00, 0x00, 0x00, 0x48])
        )
        msg = self.bus.recv(1)
        self.assertIsNone(msg)

        # write rest of first message, and then a second message
        self.serial.write(
            bytearray(
                [
                    0x65,
                    0x6C,
                    0x6C,
                    0x6F,
                    0x31,
                    0x32,
                    0x33,
                    0x08,
                    0x00,
                    0x00,
                    0x00,
                    0x0D,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x56,
                    0x34,
                    0x12,
                    0x00,
                    0xA5,
                    0xAA,
                    0xA5,
                    0xA5,
                    0xA5,
                    0x55,
                    0xA5,
                    0x55,
                    0xA5,
                    0xA5,
                    0xA5,
                    0xAA,
                    0x00,
                    0x00,
                    0x06,
                    0x00,
                    0x01,
                    0x00,
                    0xEB,
                    0x55,
                    0x55,
                ]
            )
        )
        msg = self.bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 8)
        self.assertSequenceEqual(
            msg.data, [0x48, 0x65, 0x6C, 0x6C, 0x6F, 0x31, 0x32, 0x33]
        )

        # now try to also receive 2nd message
        msg = self.bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123456)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 6)
        self.assertSequenceEqual(msg.data, [0xAA, 0xA5, 0x55, 0x55, 0xA5, 0xAA])

        # test nothing more left
        msg = self.bus.recv(1)
        self.assertIsNone(msg)
        data = self.serial.read(self.serial.in_waiting)

    def test_serial_number(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xF0,
                    0xFF,
                    0xFF,
                    0x01,
                    0x53,
                    0xFF,
                    0x6A,
                    0x06,
                    0x49,
                    0x72,
                    0x48,
                    0xA5,
                    0x55,
                    0x08,
                    0xFF,
                    0x01,
                    0x00,
                    0x11,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xF1,
                    0xFF,
                    0xFF,
                    0x01,
                    0x40,
                    0x60,
                    0x17,
                    0x87,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x00,
                    0x36,
                    0x55,
                    0x55,
                ]
            )
        )
        sn = self.bus.get_serial_number(1)
        self.assertEqual(sn, "53FF-6A06-4972-4855-4060-1787")
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xF0,
                    0xFF,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x01,
                    0xF8,
                    0x55,
                    0x55,
                    0xAA,
                    0xAA,
                    0xF1,
                    0xFF,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x01,
                    0xF9,
                    0x55,
                    0x55,
                ]
            ),
        )

        sn = self.bus.get_serial_number(0)
        self.assertIsNone(sn)
        data = self.serial.read(self.serial.in_waiting)

    def test_set_bitrate(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xD0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x40,
                    0x42,
                    0x0F,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x04,
                    0xFF,
                    0x01,
                    0x01,
                    0x64,
                    0x55,
                    0x55,
                ]
            )
        )
        self.bus.set_bitrate(1000000)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xD0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x40,
                    0x42,
                    0x0F,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x04,
                    0xFF,
                    0x01,
                    0x00,
                    0x63,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_set_auto_retransmit(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xA0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x01,
                    0xA1,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xA0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x01,
                    0xA0,
                    0x55,
                    0x55,
                ]
            )
        )
        self.bus.set_auto_retransmit(True)
        self.bus.set_auto_retransmit(False)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xA0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x00,
                    0xA0,
                    0x55,
                    0x55,
                    0xAA,
                    0xAA,
                    0xA0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x00,
                    0x9F,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_set_auto_bus_management(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xB0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x01,
                    0xB1,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xB0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x01,
                    0xB0,
                    0x55,
                    0x55,
                ]
            )
        )
        self.bus.set_auto_bus_management(True)
        self.bus.set_auto_bus_management(False)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xB0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x00,
                    0xB0,
                    0x55,
                    0x55,
                    0xAA,
                    0xAA,
                    0xB0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x01,
                    0xFF,
                    0x01,
                    0x00,
                    0xAF,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_set_serial_rate(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x90,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0xC2,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x04,
                    0xFF,
                    0x01,
                    0x01,
                    0x56,
                    0x55,
                    0x55,
                ]
            )
        )
        self.bus.set_serial_rate(115200)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0x90,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0xC2,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x04,
                    0xFF,
                    0x01,
                    0x00,
                    0xA5,
                    0x55,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_set_hw_filter(self):
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xE0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x80,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x01,
                    0x67,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xE1,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0xC0,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x01,
                    0xA8,
                    0x55,
                    0x55,
                ]
            )
        )
        self.serial.write(
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xE2,
                    0xFE,
                    0xFF,
                    0x01,
                    0xF0,
                    0x01,
                    0x00,
                    0x00,
                    0xF0,
                    0x01,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x01,
                    0xCB,
                    0x55,
                    0x55,
                ]
            )
        )
        self.bus.set_hw_filter(1, True, 0, 0, False)
        self.bus.set_hw_filter(2, True, 0, 0, True)
        self.bus.set_hw_filter(3, False, 0x1F0, 0x1F0, False)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(
            data,
            bytearray(
                [
                    0xAA,
                    0xAA,
                    0xE0,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0x80,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x00,
                    0x66,
                    0x55,
                    0x55,
                    0xAA,
                    0xAA,
                    0xE1,
                    0xFE,
                    0xFF,
                    0x01,
                    0x00,
                    0x00,
                    0x00,
                    0xC0,
                    0x00,
                    0x00,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x00,
                    0xA7,
                    0x55,
                    0x55,
                    0xAA,
                    0xAA,
                    0xE2,
                    0xFE,
                    0xFF,
                    0x01,
                    0xF0,
                    0x01,
                    0x00,
                    0x00,
                    0xF0,
                    0x01,
                    0x00,
                    0x00,
                    0x08,
                    0xFF,
                    0x01,
                    0x00,
                    0xCA,
                    0x55,
                    0x55,
                ]
            ),
        )

    def test_when_no_fileno(self):
        with self.assertRaises(NotImplementedError):
            self.bus.fileno()


if __name__ == "__main__":
    unittest.main()

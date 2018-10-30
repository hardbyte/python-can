#!/usr/bin/env python
# coding: utf-8
import unittest
import can


class slcanTestCase(unittest.TestCase):

    def setUp(self):
        self.bus = can.Bus('loop://', bustype='slcan', sleep_after_open=0)
        self.serial = self.bus.serialPortOrig
        self.serial.read(self.serial.in_waiting)

    def tearDown(self):
        self.bus.shutdown()

    def test_recv_extended(self):
        self.serial.write(b'T12ABCDEF2AA55\r')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

    def test_send_extended(self):
        msg = can.Message(arbitration_id=0x12ABCDEF,
                          is_extended_id=True,
                          data=[0xAA, 0x55])
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b'T12ABCDEF2AA55\r')

    def test_recv_standard(self):
        self.serial.write(b't4563112233\r')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x456)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 3)
        self.assertSequenceEqual(msg.data, [0x11, 0x22, 0x33])

    def test_send_standard(self):
        msg = can.Message(arbitration_id=0x456,
                          is_extended_id=False,
                          data=[0x11, 0x22, 0x33])
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b't4563112233\r')

    def test_recv_standard_remote(self):
        self.serial.write(b'r1238\r')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.is_extended_id, False)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 8)

    def test_send_standard_remote(self):
        msg = can.Message(arbitration_id=0x123,
                          is_extended_id=False,
                          is_remote_frame=True,
                          dlc=8)
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b'r1238\r')

    def test_recv_extended_remote(self):
        self.serial.write(b'R12ABCDEF6\r')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, True)
        self.assertEqual(msg.dlc, 6)

    def test_send_extended_remote(self):
        msg = can.Message(arbitration_id=0x12ABCDEF,
                          is_extended_id=True,
                          is_remote_frame=True,
                          dlc=6)
        self.bus.send(msg)
        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data, b'R12ABCDEF6\r')

    def test_partial_recv(self):
        self.serial.write(b'T12ABCDEF')
        msg = self.bus.recv(0)
        self.assertIsNone(msg)

        self.serial.write(b'2AA55\rT12')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x12ABCDEF)
        self.assertEqual(msg.is_extended_id, True)
        self.assertEqual(msg.is_remote_frame, False)
        self.assertEqual(msg.dlc, 2)
        self.assertSequenceEqual(msg.data, [0xAA, 0x55])

        msg = self.bus.recv(0)
        self.assertIsNone(msg)

        self.serial.write(b'ABCDEF2AA55\r')
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
# coding: utf-8

"""
This module tests two virtual busses attached to each other.

Some tests are skipped when run on Travis CI because they are not
reproducible, see #243 (https://github.com/hardbyte/python-can/issues/243).
"""

import os
import unittest
import time

import can

IS_TRAVIS = os.environ.get('TRAVIS', 'default') == 'true'

BITRATE = 500000
TIMEOUT = 0.1
TEST_CAN_FD = True

INTERFACE_1 = 'virtual'
CHANNEL_1 = 'vcan0'
INTERFACE_2 = 'virtual'
CHANNEL_2 = 'vcan0'


class Back2BackTestCase(unittest.TestCase):
    """
    Use two interfaces connected to the same CAN bus and test them against
    each other.
    """

    def setUp(self):
        self.bus1 = can.interface.Bus(channel=CHANNEL_1,
                                      bustype=INTERFACE_1,
                                      bitrate=BITRATE,
                                      fd=TEST_CAN_FD,
                                      single_handle=True)
        self.bus2 = can.interface.Bus(channel=CHANNEL_2,
                                      bustype=INTERFACE_2,
                                      bitrate=BITRATE,
                                      fd=TEST_CAN_FD,
                                      single_handle=True)

    def tearDown(self):
        self.bus1.shutdown()
        self.bus2.shutdown()

    def _check_received_message(self, recv_msg, sent_msg):
        self.assertIsNotNone(recv_msg,
                             "No message was received on %s" % INTERFACE_2)
        self.assertEqual(recv_msg.arbitration_id, sent_msg.arbitration_id)
        self.assertEqual(recv_msg.id_type, sent_msg.id_type)
        self.assertEqual(recv_msg.is_remote_frame, sent_msg.is_remote_frame)
        self.assertEqual(recv_msg.is_error_frame, sent_msg.is_error_frame)
        self.assertEqual(recv_msg.is_fd, sent_msg.is_fd)
        self.assertEqual(recv_msg.bitrate_switch, sent_msg.bitrate_switch)
        self.assertEqual(recv_msg.dlc, sent_msg.dlc)
        if not sent_msg.is_remote_frame:
            self.assertSequenceEqual(recv_msg.data, sent_msg.data)

    def _send_and_receive(self, msg):
        # Send with bus 1, receive with bus 2
        self.bus1.send(msg)
        recv_msg = self.bus2.recv(TIMEOUT)
        self._check_received_message(recv_msg, msg)
        # Some buses may receive their own messages. Remove it from the queue
        self.bus1.recv(0)

        # Send with bus 2, receive with bus 1
        # Add 1 to arbitration ID to make it a different message
        msg.arbitration_id += 1
        self.bus2.send(msg)
        recv_msg = self.bus1.recv(TIMEOUT)
        self._check_received_message(recv_msg, msg)

    def test_no_message(self):
        self.assertIsNone(self.bus1.recv(0.1))

    @unittest.skipIf(IS_TRAVIS, "skip on Travis CI")
    def test_timestamp(self):
        self.bus2.send(can.Message())
        recv_msg1 = self.bus1.recv(TIMEOUT)
        time.sleep(5)
        self.bus2.send(can.Message())
        recv_msg2 = self.bus1.recv(TIMEOUT)
        delta_time = recv_msg2.timestamp - recv_msg1.timestamp
        self.assertTrue(4.8 < delta_time < 5.2,
                        'Time difference should have been 5s +/- 200ms.' 
                        'But measured {}'.format(delta_time))

    def test_standard_message(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x100,
                          data=[1, 2, 3, 4, 5, 6, 7, 8])
        self._send_and_receive(msg)

    def test_extended_message(self):
        msg = can.Message(extended_id=True,
                          arbitration_id=0x123456,
                          data=[10, 11, 12, 13, 14, 15, 16, 17])
        self._send_and_receive(msg)

    def test_remote_message(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x200,
                          is_remote_frame=True,
                          dlc=4)
        self._send_and_receive(msg)

    def test_dlc_less_than_eight(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x300,
                          data=[4, 5, 6])
        self._send_and_receive(msg)

    @unittest.skipUnless(TEST_CAN_FD, "Don't test CAN-FD")
    def test_fd_message(self):
        msg = can.Message(is_fd=True,
                          extended_id=True,
                          arbitration_id=0x56789,
                          data=[0xff] * 64)
        self._send_and_receive(msg)

    @unittest.skipUnless(TEST_CAN_FD, "Don't test CAN-FD")
    def test_fd_message_with_brs(self):
        msg = can.Message(is_fd=True,
                          bitrate_switch=True,
                          extended_id=True,
                          arbitration_id=0x98765,
                          data=[0xff] * 48)
        self._send_and_receive(msg)


if __name__ == '__main__':
    unittest.main()

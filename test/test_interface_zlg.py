#!/usr/bin/env python3
# coding: utf-8

import unittest
import can

from can.exceptions import *


class ZlgTestCase(unittest.TestCase):
    def setUp(self):
        self.channel = 0
        self.device = 0
        self.std_id = 0x123
        self.ext_id = 0x123456
        self.bitrate = 500_000
        self.data_bitrate = 2_000_000
        self.bus = can.Bus(
            bustype = 'zlg',
            channel = self.channel,
            device = self.device,
            bitrate = self.bitrate,
            data_bitrate = self.data_bitrate,
        )
        self.can_std_msg = can.Message(
                arbitration_id  =   self.std_id,
                is_extended_id  =   False,
                is_fd           =   False,
                data            =   list(range(8))
        )
        self.can_ext_msg = can.Message(
                arbitration_id  =   self.ext_id,
                is_extended_id  =   True,
                is_fd           =   False,
                data            =   list(range(8))
        )
        self.canfd_std_msg = can.Message(
                arbitration_id  =   self.std_id,
                is_extended_id  =   False,
                is_fd           =   True,
                data            =   list(range(64))
        )
        self.canfd_ext_msg = can.Message(
                arbitration_id  =   self.ext_id,
                is_extended_id  =   True,
                is_fd           =   True,
                data            =   list(range(64))
        )

    def tearDown(self):
        self.bus.shutdown()

    def test_send_can_std(self):
        try:
            self.bus.send(self.can_std_msg)
        except CanOperationError as ex:
            self.fail('Failed to send CAN std frame')

    def test_send_can_ext(self):
        try:
            self.bus.send(self.can_ext_msg)
        except CanOperationError as ex:
            self.fail('Failed to send CAN ext frame')

    def test_send_canfd_std(self):
        try:
            self.bus.send(self.canfd_std_msg)
        except CanOperationError as ex:
            self.fail('Failed to send CANFD std frame')

    def test_send_canfd_ext(self):
        try:
            self.bus.send(self.canfd_ext_msg)
        except CanOperationError as ex:
            self.fail('Failed to send CANFD ext frame')

    def test_recv(self):
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)


if __name__ == "__main__":
    unittest.main()

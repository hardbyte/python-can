#!/usr/bin/env python
# coding: utf-8

"""
"""

from time import sleep
import unittest
import logging

import can

logging.getLogger(__file__).setLevel(logging.DEBUG)


class ZeroDLCTest(unittest.TestCase):

    def test_recv_non_zero_dlc(self):
        bus_send = can.interface.Bus(bustype='virtual')
        bus_recv = can.interface.Bus(bustype='virtual')
        data = [0, 1, 2, 3, 4, 5, 6, 7]
        msg_send = can.Message(is_extended_id=False, arbitration_id=0x100, data=data)

        bus_send.send(msg_send)
        msg_recv = bus_recv.recv()

        # Receiving a frame with data should evaluate msg_recv to True
        self.assertTrue(msg_recv)

    def test_recv_none(self):
        bus_recv = can.interface.Bus(bustype='virtual')

        msg_recv = bus_recv.recv(timeout=0)

        # Receiving nothing should evaluate msg_recv to False
        self.assertFalse(msg_recv)

    def test_recv_zero_dlc(self):
        bus_send = can.interface.Bus(bustype='virtual')
        bus_recv = can.interface.Bus(bustype='virtual')
        msg_send = can.Message(is_extended_id=False, arbitration_id=0x100, data=[])

        bus_send.send(msg_send)
        msg_recv = bus_recv.recv()

        # Receiving a frame without data (dlc == 0) should evaluate msg_recv to True
        self.assertTrue(msg_recv)


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python
# coding: utf-8

"""
This module tests the context manager of Bus and Notifier classes
"""

import unittest
import can


class ContextManagerTest(unittest.TestCase):

    def setUp(self):
        data = [0, 1, 2, 3, 4, 5, 6, 7]
        self.msg_send = can.Message(is_extended_id=False, arbitration_id=0x100, data=data)

    def test_open_buses(self):
        with can.Bus(interface='virtual') as bus_send, can.Bus(interface='virtual') as bus_recv:
            bus_send.send(self.msg_send)
            msg_recv = bus_recv.recv()

            # Receiving a frame with data should evaluate msg_recv to True
            self.assertTrue(msg_recv)

    def test_use_closed_bus(self):
        with can.Bus(interface='virtual') as bus_send, can.Bus(interface='virtual') as bus_recv:
            bus_send.send(self.msg_send)

        # Receiving a frame after bus has been closed should raise a CanException
        self.assertRaises(can.CanError, bus_recv.recv)
        self.assertRaises(can.CanError, bus_send.send, self.msg_send)


if __name__ == '__main__':
    unittest.main()

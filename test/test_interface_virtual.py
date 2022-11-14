#!/usr/bin/env python
# coding: utf-8

"""
This module tests :meth:`can.interface.virtual`.
"""

import unittest

from can import Bus, Message

EXAMPLE_MSG1 = Message(timestamp=1639739471.5565314, arbitration_id=0x481, data=b"\x01")


class TestMessageFiltering(unittest.TestCase):
    def setUp(self):
        self.node1 = Bus("test", bustype="virtual", preserve_timestamps=True)
        self.node2 = Bus("test", bustype="virtual")

    def tearDown(self):
        self.node1.shutdown()
        self.node2.shutdown()

    def test_sendmsg(self):
        self.node2.send(EXAMPLE_MSG1)
        r = self.node1.recv(0.1)
        assert r.timestamp != EXAMPLE_MSG1.timestamp
        assert r.arbitration_id == EXAMPLE_MSG1.arbitration_id
        assert r.data == EXAMPLE_MSG1.data

    def test_sendmsg_preserve_timestamp(self):
        self.node1.send(EXAMPLE_MSG1)
        r = self.node2.recv(0.1)
        assert r.timestamp == EXAMPLE_MSG1.timestamp
        assert r.arbitration_id == EXAMPLE_MSG1.arbitration_id
        assert r.data == EXAMPLE_MSG1.data


if __name__ == "__main__":
    unittest.main()

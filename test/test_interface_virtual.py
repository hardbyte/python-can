#!/usr/bin/env python

"""
This module tests :meth:`can.interface.virtual`.
"""

import unittest

import pytest

from can import Bus, CanOperationError, Message

EXAMPLE_MSG1 = Message(timestamp=1639739471.5565314, arbitration_id=0x481, data=b"\x01")


class TestMessageFiltering(unittest.TestCase):
    def setUp(self):
        self.node1 = Bus("test", interface="virtual", preserve_timestamps=True)
        self.node2 = Bus("test", interface="virtual")

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


def test_listen_only() -> None:
    """
    Test Scope:
        Listen-only mode of the virtual interface.
    Preconditions:
        A listen-only bus and a normal bus on the same virtual channel.
    Events:
        The normal bus sends a message, then the listen-only bus tries to send one
        and to switch listen_only off.
    Evaluate:
        Only the listen-only bus reports listen_only, it receives the message,
        its own send raises CanOperationError and nothing reaches the normal bus.
        Setting listen_only raises NotImplementedError.
    """
    with (
        Bus("listen_only", interface="virtual", listen_only=True) as listener,
        Bus("listen_only", interface="virtual") as sender,
    ):
        assert listener.listen_only
        assert not sender.listen_only

        sender.send(EXAMPLE_MSG1)
        received = listener.recv(0.1)
        assert received is not None
        assert received.arbitration_id == EXAMPLE_MSG1.arbitration_id

        with pytest.raises(CanOperationError):
            listener.send(EXAMPLE_MSG1)
        assert sender.recv(0) is None

        with pytest.raises(NotImplementedError):
            listener.listen_only = False


if __name__ == "__main__":
    unittest.main()

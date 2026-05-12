#!/usr/bin/env python

"""
Regression tests for https://github.com/hardbyte/python-can/issues/2053.

``SocketcanBus`` previously used ``select.select()``, which is limited by
glibc to file descriptors below ``FD_SETSIZE`` (1024) and raises
``ValueError: filedescriptor out of range in select()`` for higher fds.

These tests verify that ``send()`` and ``recv()`` work with a socket whose
file descriptor exceeds 1023.
"""

import unittest
from unittest.mock import MagicMock, patch

import can
from can import Message
from can.interfaces.socketcan.socketcan import build_can_frame

from .config import IS_LINUX

HIGH_FD = 2048


@unittest.skipUnless(IS_LINUX, "socketcan is only available on Linux")
class TestSocketcanHighFdLinux(unittest.TestCase):
    """Verify SocketcanBus works when the underlying socket fd exceeds 1023."""

    def setUp(self):
        patcher_create = patch("can.interfaces.socketcan.socketcan.create_socket")
        patcher_bind = patch("can.interfaces.socketcan.socketcan.bind_socket")

        self.mock_create_socket = patcher_create.start()
        self.mock_bind_socket = patcher_bind.start()

        self.mock_socket = MagicMock()
        self.mock_socket.fileno.return_value = HIGH_FD
        self.mock_create_socket.return_value = self.mock_socket

        self.bus = can.Bus(interface="socketcan", channel="can0")

        self.addCleanup(patcher_create.stop)
        self.addCleanup(patcher_bind.stop)

    def tearDown(self):
        self.bus.shutdown()

    @patch("can.interfaces.socketcan.socketcan.select.poll")
    def test_send_high_fd(self, mock_poll_factory):
        """send() succeeds when the socket fd > 1023."""
        poller = MagicMock()
        # ``poll()`` returns a non-empty list to signal write readiness.
        poller.poll.return_value = [(HIGH_FD, 4)]
        mock_poll_factory.return_value = poller

        msg = Message(arbitration_id=0x123, data=[1, 2, 3, 4, 5, 6, 7, 8])
        frame_data = build_can_frame(msg)
        self.mock_socket.send.return_value = len(frame_data)

        self.bus.send(msg)

        self.mock_socket.send.assert_called_once_with(frame_data)
        poller.register.assert_called_once()

    @patch("can.interfaces.socketcan.socketcan.capture_message")
    @patch("can.interfaces.socketcan.socketcan.select.poll")
    def test_recv_high_fd(self, mock_poll_factory, mock_capture):
        """recv() succeeds when the socket fd > 1023."""
        poller = MagicMock()
        poller.poll.return_value = [(HIGH_FD, 1)]
        mock_poll_factory.return_value = poller

        expected_msg = Message(
            arbitration_id=0x123,
            data=[1, 2, 3, 4, 5, 6, 7, 8],
            channel="can0",
            timestamp=1000.0,
        )
        mock_capture.return_value = expected_msg

        msg = self.bus.recv(timeout=1.0)

        self.assertIsNotNone(msg)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.data, bytearray([1, 2, 3, 4, 5, 6, 7, 8]))
        mock_capture.assert_called_once_with(self.mock_socket, False)


if __name__ == "__main__":
    unittest.main()

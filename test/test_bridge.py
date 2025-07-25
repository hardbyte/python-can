#!/usr/bin/env python

"""
This module tests the functions inside of bridge.py
"""

import random
import string
import sys
import threading
import time
from time import sleep as real_sleep
import unittest.mock

import can
import can.bridge
from can.interfaces import virtual

from .message_helper import ComparingMessagesTestCase


class TestBridgeScriptModule(unittest.TestCase, ComparingMessagesTestCase):

    TIMEOUT = 3.0

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        ComparingMessagesTestCase.__init__(
            self,
            allowed_timestamp_delta=None,
            preserves_channel=False,
        )

    def setUp(self) -> None:
        self.stop_event = threading.Event()

        self.channel1 = "".join(random.choices(string.ascii_letters, k=8))
        self.channel2 = "".join(random.choices(string.ascii_letters, k=8))

        self.cli_args = [
            "--bus1-interface",
            "virtual",
            "--bus1-channel",
            self.channel1,
            "--bus2-interface",
            "virtual",
            "--bus2-channel",
            self.channel2,
        ]

        self.testmsg = can.Message(
            arbitration_id=0xC0FFEE, data=[0, 25, 0, 1, 3, 1, 4, 1], is_extended_id=True
        )

    def fake_sleep(self, duration):
        """A fake replacement for time.sleep that checks periodically
        whether self.stop_event is set, and raises KeyboardInterrupt
        if so.

        This allows tests to simulate an interrupt (like Ctrl+C)
        during long sleeps, in a controlled and responsive way.
        """
        interval = 0.05  # Small interval for responsiveness
        t_wakeup = time.perf_counter() + duration
        while time.perf_counter() < t_wakeup:
            if self.stop_event.is_set():
                raise KeyboardInterrupt("Simulated interrupt from fake_sleep")
            real_sleep(interval)

    def test_bridge(self):
        with (
            unittest.mock.patch("can.bridge.time.sleep", new=self.fake_sleep),
            unittest.mock.patch("can.bridge.sys.argv", [sys.argv[0], *self.cli_args]),
        ):
            # start script
            thread = threading.Thread(target=can.bridge.main)
            thread.start()

            # wait until script instantiates virtual buses
            t0 = time.perf_counter()
            while True:
                with virtual.channels_lock:
                    if (
                        self.channel1 in virtual.channels
                        and self.channel2 in virtual.channels
                    ):
                        break
                if time.perf_counter() > t0 + 2.0:
                    raise TimeoutError("Bridge script did not create virtual buses")
                real_sleep(0.2)

            # create buses with the same channels as in scripts
            with (
                can.interfaces.virtual.VirtualBus(self.channel1) as bus1,
                can.interfaces.virtual.VirtualBus(self.channel2) as bus2,
            ):
                # send test message to bus1, it should be received on bus2
                bus1.send(self.testmsg)
                recv_msg = bus2.recv(self.TIMEOUT)
                self.assertMessageEqual(self.testmsg, recv_msg)

                # assert that both buses are empty
                self.assertIsNone(bus1.recv(0))
                self.assertIsNone(bus2.recv(0))

                # send test message to bus2, it should be received on bus1
                bus2.send(self.testmsg)
                recv_msg = bus1.recv(self.TIMEOUT)
                self.assertMessageEqual(self.testmsg, recv_msg)

                # assert that both buses are empty
                self.assertIsNone(bus1.recv(0))
                self.assertIsNone(bus2.recv(0))

            # stop the bridge script
            self.stop_event.set()
            thread.join()

            # assert that the virtual buses were closed
            with virtual.channels_lock:
                self.assertNotIn(self.channel1, virtual.channels)
                self.assertNotIn(self.channel2, virtual.channels)


if __name__ == "__main__":
    unittest.main()

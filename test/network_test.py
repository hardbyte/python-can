#!/usr/bin/env python
import contextlib
import logging
import random
import threading
import unittest

import can
from test.config import IS_PYPY

logging.getLogger(__file__).setLevel(logging.WARNING)


# make a random bool:
def rbool():
    return random.choice([False, True])


class ControllerAreaNetworkTestCase(unittest.TestCase):
    """
    This test ensures that what messages go in to the bus is what comes out.

    Requires a can interface.

    To ensure that hardware and/or software message priority queues don't
    effect the test, messages are sent one at a time.
    """

    num_messages = 512

    # TODO check if error flags are working (don't currently appear on bus)
    error_flags = [False for _ in range(num_messages)]

    remote_flags = [rbool() for _ in range(num_messages)]
    extended_flags = [rbool() for _ in range(num_messages)]

    ids = list(range(num_messages))
    data = list(
        bytearray([random.randrange(0, 2**8 - 1) for a in range(random.randrange(9))])
        for b in range(num_messages)
    )

    def setUp(self):
        # Save all can.rc defaults
        self._can_rc = can.rc
        can.rc = {"interface": "virtual"}

    def tearDown(self):
        # Restore the defaults
        can.rc = self._can_rc

    def producer(self, channel: str):
        with can.interface.Bus(channel=channel) as client_bus:
            for i in range(self.num_messages):
                m = can.Message(
                    arbitration_id=self.ids[i],
                    is_remote_frame=self.remote_flags[i],
                    is_error_frame=self.error_flags[i],
                    is_extended_id=self.extended_flags[i],
                    data=self.data[i],
                )
                client_bus.send(m)

    def testProducer(self):
        """Verify that we can send arbitrary messages on the bus"""
        logging.debug("testing producer alone")
        self.producer(channel="testProducer")
        logging.debug("producer test complete")

    def testProducerConsumer(self):
        logging.debug("testing producer/consumer")
        read_timeout = 2.0 if IS_PYPY else 0.5
        channel = "testProducerConsumer"

        with can.interface.Bus(channel=channel, interface="virtual") as server_bus:
            t = threading.Thread(target=self.producer, args=(channel,))
            t.start()

            i = 0
            while i < self.num_messages:
                msg = server_bus.recv(timeout=read_timeout)
                self.assertIsNotNone(msg, "Didn't receive a message")

                self.assertEqual(msg.is_extended_id, self.extended_flags[i])
                if not msg.is_remote_frame:
                    self.assertEqual(msg.data, self.data[i])
                self.assertEqual(msg.arbitration_id, self.ids[i])

                self.assertEqual(msg.is_error_frame, self.error_flags[i])
                self.assertEqual(msg.is_remote_frame, self.remote_flags[i])

                i += 1
            t.join()

            with contextlib.suppress(NotImplementedError):
                server_bus.flush_tx_buffer()


if __name__ == "__main__":
    unittest.main()

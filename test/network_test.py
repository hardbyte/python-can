from __future__ import print_function

import unittest
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import random

import logging
logging.getLogger(__file__).setLevel(logging.WARNING)

# make a random bool:
rbool = lambda: bool(round(random.random()))

channel = 'vcan0'
import can
can.rc['interface'] = 'socketcan_ctypes'


class ControllerAreaNetworkTestCase(unittest.TestCase):

    """
    This test ensures that what messages go in to the bus is what comes out.
    It relies on a vcan0 interface.

    To ensure that hardware and/or software message priority queues don't
    effect the test, messages are sent one at a time.
    """

    num_messages = 512

    # TODO check if error flags are working (don't currently appear on bus)
    error_flags = [False for _ in range(num_messages)]

    remote_flags = [rbool() for _ in range(num_messages)]
    extended_flags = [rbool() for _ in range(num_messages)]

    ids = list(range(num_messages))
    data = list(bytearray([random.randrange(0, 2 ** 8 - 1)
                           for a in range(random.randrange(9))])
                for b in range(num_messages))

    def producer(self, ready_event, msg_read):
        self.client_bus = can.interface.Bus(channel=channel)
        ready_event.wait()
        for i in range(self.num_messages):
            m = can.Message(
                arbitration_id=self.ids[i],
                is_remote_frame=self.remote_flags[i],
                is_error_frame=self.error_flags[i],
                extended_id=self.extended_flags[i],
                data=self.data[i]
            )
            logging.debug("writing message: {}".format(m))
            #logging.debug("DATA: {}".format(self.data[i]))
            # Don't send until the other thread is ready
            msg_read.wait()
            msg_read.clear()
            self.client_bus.send(m)

    def _testProducer(self):
        """Verify that we can send arbitrary messages on the bus"""
        logging.debug("testing producer alone")
        self.producer()
        logging.debug("producer test complete")

    def testProducerConsumer(self):
        logging.debug("testing producer/consumer")
        ready = threading.Event()
        msg_read = threading.Event()

        self.server_bus = can.interface.Bus(channel=channel)

        t = threading.Thread(target=self.producer, args=(ready, msg_read))
        t.start()

        # Ensure there are no messages on the bus
        while True:
            m = self.server_bus.recv(timeout=0.5)
            if m is None:
                print("No messages... lets go")
                break
            else:
                print("received messages before the test has started...")
                self.assertTrue(False)
        ready.set()
        i = 0
        while i < self.num_messages:
            msg_read.set()
            msg = self.server_bus.recv(timeout=0.5)
            self.assertIsNotNone(msg, "Didn't receive a message")
            logging.debug("Received message {} with data: {}".format(i, msg.data))

            self.assertEqual(msg.id_type, self.extended_flags[i])
            self.assertEqual(msg.data, self.data[i])
            self.assertEqual(msg.arbitration_id, self.ids[i])

            self.assertEqual(msg.is_error_frame, self.error_flags[i])
            self.assertEqual(msg.is_remote_frame, self.remote_flags[i])

            i += 1
        t.join()

        self.server_bus.flush_tx_buffer()
        self.server_bus.shutdown()

if __name__ == '__main__':
    unittest.main()

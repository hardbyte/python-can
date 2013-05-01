import unittest
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import random
import time


import can
can.rc['interface'] = 'socketcan_native'
from can.interfaces.interface import Bus
can_interface = 'vcan0'

import logging
logging.getLogger(__file__).setLevel(logging.DEBUG)

# make a random bool:
rbool = lambda: bool(round(random.random()))


class ControllerAreaNetworkTestCase(unittest.TestCase):
    """
    This test ensures that what messages go in to the bus is what comes out.
    It relies on a vcan0 interface.
    """

    num_messages = 400

    # TODO check if error flags are working (don't currently appear on bus)
    error_flags = [False for _ in range(num_messages)]

    remote_flags = [rbool() for _ in range(num_messages)]
    extended_flags = [rbool() for _ in range(num_messages)]

    ids = list(range(num_messages))
    data = list(bytes([random.randrange(0, 2 ** 8 - 1)
                       for a in range(random.randrange(9))])
                for b in range(num_messages))


    def producer(self):
        self.client_bus = Bus(can_interface)
        for i in range(self.num_messages):
            m = can.Message(
                arbitration_id=self.ids[i],
                is_remote_frame=self.remote_flags[i],
                is_error_frame=self.error_flags[i],
                extended_id=self.extended_flags[i],
                data=self.data[i]
            )
            logging.debug("writing message: {}".format(m))
            self.client_bus.send(m)
            logging.debug("message written")

    def testProducer(self):
        """Verify that we can send arbitrary messages on the bus"""
        logging.debug("testing producer alone")
        self.producer()
        logging.debug("producer test complete")

    def testProducerConsumer(self):
        logging.debug("testing producer/consumer")
        self.server_bus = Bus(can_interface)

        t = threading.Thread(target=self.producer)
        t.start()

        # TODO this test currently fails because of a threading issue with the __iter__ api versus
        # the listener api in bus.
        for i, msg in enumerate(self.server_bus):
            logging.debug("Received a message...")
            self.assertEqual(msg.is_error_frame, self.error_flags[i])
            self.assertEqual(msg.is_remote_frame, self.remote_flags[i])
            self.assertEqual(msg.id_type, self.extended_flags[i])
            self.assertEqual(msg.data, self.data[i])
            self.assertEqual(msg.arbitration_id, self.ids[i])

            logging.debug("Message {} checked out ok".format(i))

            if i == self.num_messages - 1:
                logging.debug("Server done now...")
                t.join()
                return

        self.server_bus.flush_tx_buffer()
        self.server_bus.shutdown()

if __name__ == '__main__':
    unittest.main()

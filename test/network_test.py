import unittest
import threading
try:
    import queue
except ImportError:
    import Queue as queue
import random
import time


import can
from can.interfaces.interface import Bus
can_interface = 'vcan0'

import logging
logging.getLogger(__file__).setLevel(logging.WARNING)

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

    def producer(self, ready_event):
        self.client_bus = Bus(can_interface)
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
            self.client_bus.send(m)

    def _testProducer(self):
        """Verify that we can send arbitrary messages on the bus"""
        logging.debug("testing producer alone")
        self.producer()
        logging.debug("producer test complete")

    def testProducerConsumer(self):
        logging.debug("testing producer/consumer")
        ready = threading.Event()
        self.server_bus = Bus(can_interface)

        t = threading.Thread(target=self.producer, args=(ready,))
        t.start()
        
        # TODO Ensure there are no messages on the bus
        #while True:
        #    m = self.server_bus.recv(timeout=0.05)
        #    if m == None: 
        #        print("No messages... lets go")
        #        break
        #    else:
        #        print("received message...")
        ready.set()
        for i, msg in enumerate(self.server_bus):
            
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

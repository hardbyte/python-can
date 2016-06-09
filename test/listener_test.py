from time import sleep
import unittest
import threading
from sys import version_info

try:
    import queue
except ImportError:
    import Queue as queue
import random


import can

import logging
logging.getLogger("").setLevel(logging.DEBUG)


def generate_message(arbitration_id):
    data = [random.randrange(0, 2 ** 8 - 1) for b in range(8)]
    m = can.Message(arbitration_id=arbitration_id, data=data, extended_id=False)
    return m


class ListenerImportTest(unittest.TestCase):

    def testClassesImportable(self):
        assert hasattr(can, 'Listener')
        assert hasattr(can, 'BufferedReader')
        assert hasattr(can, 'Notifier')


class ListenerTest(unittest.TestCase):

    def setUp(self):
        self.bus = bus = can.interface.Bus()

    def tearDown(self):
        self.bus.shutdown()
        del self.bus
        sleep(0.5)

    def testBasicListenerCanBeAddedToNotifier(self):
        notifier = can.Notifier(self.bus, [can.Listener()])


    def testBasicListenerWithMesg(self):
        a_listener = can.Listener()
        notifier = can.Notifier(self.bus, [a_listener])
        self.bus.send(generate_message(0xDADADA))

    def testBufferedListenerReceives(self):
        a_listener = can.BufferedReader()
        notifier = can.Notifier(self.bus, [a_listener])
        m = a_listener.get_message(0.2)
        self.bus.send(generate_message(0xDADADA))
        sleep(0.50)
        self.assertIsNotNone(m)


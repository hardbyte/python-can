#!/usr/bin/env python
# coding: utf-8

"""
This module tests cyclic send tasks.
"""

from __future__ import absolute_import

from time import sleep
import unittest

import can

from .config import *

class SimpleCyclicSendTaskTest(unittest.TestCase):

    @unittest.skipIf(IS_CI, "the timing sensitive behaviour cannot be reproduced reliably on a CI server")
    def test_cycle_time(self):
        msg = can.Message(extended_id=False, arbitration_id=0x100, data=[0,1,2,3,4,5,6,7])
        bus1 = can.interface.Bus(bustype='virtual')
        bus2 = can.interface.Bus(bustype='virtual')
        task = bus1.send_periodic(msg, 0.01, 1)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        sleep(5)
        size = bus2.queue.qsize()
        # About 100 messages should have been transmitted
        self.assertTrue(90 < size < 110,
                        '100 +/- 10 messages should have been transmitted. But queue contained {}'.format(size))
        last_msg = bus2.recv()
        self.assertEqual(last_msg, msg)

        bus1.shutdown()
        bus2.shutdown()

if __name__ == '__main__':
    unittest.main()

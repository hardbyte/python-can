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
        msg = can.Message(extended_id=False, arbitration_id=0x123, data=[0,1,2,3,4,5,6,7])
        bus1 = can.interface.Bus(bustype='virtual')
        bus2 = can.interface.Bus(bustype='virtual')
        task = bus1.send_periodic(msg, 0.01, 1)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        sleep(2)
        size = bus2.queue.qsize()
        # About 100 messages should have been transmitted
        self.assertTrue(80 <= size <= 120,
                        '100 +/- 20 messages should have been transmitted. But queue contained {}'.format(size))
        last_msg = bus2.recv()
        self.assertEqual(last_msg, msg)

        bus1.shutdown()
        bus2.shutdown()


    @unittest.skipIf(IS_CI, "the timing sensitive behaviour cannot be reproduced reliably on a CI server")
    def test_removing_bus_tasks(self):

        bus1 = can.interface.Bus(bustype='virtual')
        bus2 = can.interface.Bus(bustype='virtual')
        tasks = []
        for task_i in range(10):
            msg = can.Message(extended_id=False, arbitration_id=0x123, data=[0, 1, 2, 3, 4, 5, 6, 7])
            msg.arbitration_id = task_i
            task = bus1.send_periodic(msg, 0.1, 1)
            tasks.append(task)
            self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        assert len(bus1._periodic_tasks) == 10

        for task in tasks:
            task.stop()

        assert len(bus1._periodic_tasks) == 0

        bus1.shutdown()
        bus2.shutdown()


if __name__ == '__main__':
    unittest.main()

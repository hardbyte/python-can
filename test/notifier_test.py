#!/usr/bin/env python
# coding: utf-8

import unittest
import time
try:
    import asyncio
except ImportError:
    asyncio = None

import can


class NotifierTest(unittest.TestCase):

    def test_single_bus(self):
        bus = can.Bus('test', bustype='virtual', receive_own_messages=True)
        reader = can.BufferedReader()
        notifier = can.Notifier(bus, [reader], 0.1)
        msg = can.Message()
        bus.send(msg)
        self.assertIsNotNone(reader.get_message(1))
        notifier.stop()
        bus.shutdown()

    def test_multiple_bus(self):
        bus1 = can.Bus(0, bustype='virtual', receive_own_messages=True)
        bus2 = can.Bus(1, bustype='virtual', receive_own_messages=True)
        reader = can.BufferedReader()
        notifier = can.Notifier([bus1, bus2], [reader], 0.1)
        msg = can.Message()
        bus1.send(msg)
        time.sleep(0.1)
        bus2.send(msg)
        recv_msg = reader.get_message(1)
        self.assertIsNotNone(recv_msg)
        self.assertEqual(recv_msg.channel, 0)
        recv_msg = reader.get_message(1)
        self.assertIsNotNone(recv_msg)
        self.assertEqual(recv_msg.channel, 1)
        notifier.stop()
        bus1.shutdown()
        bus2.shutdown()


class AsyncNotifierTest(unittest.TestCase):

    @unittest.skipIf(asyncio is None, 'Test requires asyncio')
    def test_asyncio_notifier(self):
        loop = asyncio.get_event_loop()
        bus = can.Bus('test', bustype='virtual', receive_own_messages=True)
        reader = can.AsyncBufferedReader()
        notifier = can.Notifier(bus, [reader], 0.1, loop=loop)
        msg = can.Message()
        bus.send(msg)
        future = asyncio.wait_for(reader.get_message(), 1.0)
        recv_msg = loop.run_until_complete(future)
        self.assertIsNotNone(recv_msg)
        notifier.stop()
        bus.shutdown()



if __name__ == '__main__':
    unittest.main()

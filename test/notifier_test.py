#!/usr/bin/env python

import unittest
import time
import asyncio

import can


class NotifierTest(unittest.TestCase):
    def test_single_bus(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            reader = can.BufferedReader()
            notifier = can.Notifier(bus, [reader], 0.1)
            msg = can.Message()
            bus.send(msg)
            self.assertIsNotNone(reader.get_message(1))
            notifier.stop()

    def test_multiple_bus(self):
        with can.Bus(0, interface="virtual", receive_own_messages=True) as bus1:
            with can.Bus(1, interface="virtual", receive_own_messages=True) as bus2:
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


class AsyncNotifierTest(unittest.TestCase):
    def test_asyncio_notifier(self):
        async def run_it():
            with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
                reader = can.AsyncBufferedReader()
                notifier = can.Notifier(
                    bus, [reader], 0.1, loop=asyncio.get_running_loop()
                )
                bus.send(can.Message())
                recv_msg = await asyncio.wait_for(reader.get_message(), 0.5)
                self.assertIsNotNone(recv_msg)
                notifier.stop()

        asyncio.run(run_it())


if __name__ == "__main__":
    unittest.main()

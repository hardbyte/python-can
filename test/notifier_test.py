#!/usr/bin/env python

import asyncio
import time
import unittest

import can


class RaisingListener(can.Listener):
    def on_message_received(self, msg: can.Message) -> None:
        raise ValueError("listener failed")


class ErrorCollector(can.Listener):
    def __init__(self, event: asyncio.Event) -> None:
        self.event = event
        self.errors: list[Exception] = []

    def on_message_received(self, msg: can.Message) -> None:
        pass

    def on_error(self, exc: Exception) -> None:
        self.errors.append(exc)
        self.event.set()


class NotifierTest(unittest.TestCase):
    def test_single_bus(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            reader = can.BufferedReader()
            notifier = can.Notifier(bus, [reader], 0.1)
            self.assertFalse(notifier.stopped)
            msg = can.Message()
            bus.send(msg)
            self.assertIsNotNone(reader.get_message(1))
            notifier.stop()
            self.assertTrue(notifier.stopped)

    def test_multiple_bus(self):
        with (
            can.Bus(0, interface="virtual", receive_own_messages=True) as bus1,
            can.Bus(1, interface="virtual", receive_own_messages=True) as bus2,
        ):
            reader = can.BufferedReader()
            notifier = can.Notifier([bus1, bus2], [reader], 0.1)
            self.assertFalse(notifier.stopped)
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
            self.assertTrue(notifier.stopped)

    def test_context_manager(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            reader = can.BufferedReader()
            with can.Notifier(bus, [reader], 0.1) as notifier:
                self.assertFalse(notifier.stopped)
                msg = can.Message()
                bus.send(msg)
                self.assertIsNotNone(reader.get_message(1))
                notifier.stop()
                self.assertTrue(notifier.stopped)

    def test_registry(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            reader = can.BufferedReader()
            with can.Notifier(bus, [reader], 0.1) as notifier:
                # creating a second notifier for the same bus must fail
                self.assertRaises(ValueError, can.Notifier, bus, [reader], 0.1)

                # find_instance must return the existing instance
                self.assertEqual(can.Notifier.find_instances(bus), (notifier,))

            # Notifier is stopped, find_instances() must return an empty tuple
            self.assertEqual(can.Notifier.find_instances(bus), ())

            # now the first notifier is stopped, a new notifier can be created without error:
            with can.Notifier(bus, [reader], 0.1) as notifier:
                # the next notifier call should fail again since there is an active notifier already
                self.assertRaises(ValueError, can.Notifier, bus, [reader], 0.1)

                # find_instance must return the existing instance
                self.assertEqual(can.Notifier.find_instances(bus), (notifier,))


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

    def test_sync_listener_error_calls_on_error_with_loop(self):
        async def run_it():
            event = asyncio.Event()
            collector = ErrorCollector(event)
            with can.Bus(
                "sync-listener-error", interface="virtual", receive_own_messages=True
            ) as bus:
                notifier = can.Notifier(
                    bus,
                    [RaisingListener(), collector],
                    0.1,
                    loop=asyncio.get_running_loop(),
                )
                try:
                    bus.send(can.Message())
                    await asyncio.wait_for(event.wait(), 0.5)
                    self.assertEqual(len(collector.errors), 1)
                    self.assertIsInstance(collector.errors[0], ValueError)
                    self.assertIs(notifier.exception, collector.errors[0])
                finally:
                    notifier.stop()

        asyncio.run(run_it())

    def test_async_listener_error_calls_on_error(self):
        async def run_it():
            event = asyncio.Event()
            collector = ErrorCollector(event)

            async def raising_callback(msg: can.Message) -> None:
                raise RuntimeError("async listener failed")

            with can.Bus(
                "async-listener-error", interface="virtual", receive_own_messages=True
            ) as bus:
                notifier = can.Notifier(
                    bus,
                    [raising_callback, collector],
                    0.1,
                    loop=asyncio.get_running_loop(),
                )
                try:
                    bus.send(can.Message())
                    await asyncio.wait_for(event.wait(), 0.5)
                    self.assertEqual(len(collector.errors), 1)
                    self.assertIsInstance(collector.errors[0], RuntimeError)
                    self.assertIs(notifier.exception, collector.errors[0])
                finally:
                    notifier.stop()

        asyncio.run(run_it())


if __name__ == "__main__":
    unittest.main()

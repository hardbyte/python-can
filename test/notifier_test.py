#!/usr/bin/env python

import asyncio
import io
import time
import unittest

import can


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
    def test_queued_message_is_not_delivered_after_stop(self):
        async def run_it():
            loop = asyncio.get_running_loop()
            errors = []
            loop.set_exception_handler(lambda loop, context: errors.append(context))
            stream = io.StringIO()
            writer = can.CanutilsLogWriter(stream)
            reader = can.BufferedReader()
            notifier = can.Notifier([], [writer, reader], loop=loop)
            delivered = can.Message(
                arbitration_id=0x123, is_extended_id=False, data=[0x12]
            )
            queued = can.Message(
                arbitration_id=0x456, is_extended_id=False, data=[0x34]
            )
            try:
                loop.call_soon_threadsafe(notifier._on_message_received, delivered)
                await asyncio.sleep(0)
                self.assertIn("123#12", stream.getvalue())

                loop.call_soon_threadsafe(notifier._on_message_received, queued)
                notifier.stop()
                await asyncio.sleep(0)

                self.assertTrue(stream.closed)
                self.assertIs(reader.get_message(timeout=0), delivered)
                self.assertIsNone(reader.get_message(timeout=0))
                self.assertEqual(errors, [])
            finally:
                notifier.stop()

        asyncio.run(run_it())

    def test_listener_can_stop_delivery_to_remaining_listeners(self):
        async def run_it():
            delivered = []

            def stop_and_record(msg):
                delivered.append(msg)
                notifier.stop()

            notifier = can.Notifier(
                [],
                [stop_and_record, lambda msg: stop_and_record(msg)],
                loop=asyncio.get_running_loop(),
            )
            message = can.Message()
            try:
                notifier._on_message_received(message)
                self.assertEqual(delivered, [message])
                self.assertTrue(notifier.stopped)
            finally:
                notifier.stop()

        asyncio.run(run_it())

    def test_active_listener_error_is_reported_to_event_loop(self):
        async def run_it():
            loop = asyncio.get_running_loop()
            errors = []
            loop.set_exception_handler(lambda loop, context: errors.append(context))

            def raising_listener(msg):
                raise ValueError("active listener failed")

            notifier = can.Notifier([], [raising_listener], loop=loop)
            try:
                loop.call_soon_threadsafe(notifier._on_message_received, can.Message())
                await asyncio.sleep(0)
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0]["exception"], ValueError)
                self.assertEqual(str(errors[0]["exception"]), "active listener failed")
            finally:
                notifier.stop()

        asyncio.run(run_it())

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

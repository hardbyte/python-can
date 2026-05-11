#!/usr/bin/env python

import asyncio
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

    def test_restart(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            reader = can.BufferedReader()
            notifier = can.Notifier(bus, [reader], 0.1)
            
            bus.send(can.Message(arbitration_id=0x123))
            self.assertIsNotNone(reader.get_message(1))
            
            notifier.stop()
            self.assertTrue(notifier.stopped)
            
            new_reader = can.BufferedReader()
            notifier.listeners = [new_reader]
            
            notifier.restart()
            self.assertFalse(notifier.stopped)
            
            # Small settling time for the thread to actually start
            time.sleep(0.2)
            
            # Send and Verify
            msg = can.Message(arbitration_id=0xABC)
            bus.send(msg)
            
            recv = new_reader.get_message(1)
            self.assertIsNotNone(recv, "Failed to receive message after restart")
            self.assertEqual(recv.arbitration_id, 0xABC)
            
            notifier.stop()

    def test_restart_registry_lifecycle(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            notifier = can.Notifier(bus, [], 0.1)
            notifier.stop()
            
            # Verify it is removed from registry
            self.assertEqual(can.Notifier.find_instances(bus), ())
            
            notifier.restart()
            
            # Verify it is back in the registry and blocking others
            self.assertEqual(can.Notifier.find_instances(bus), (notifier,))
            self.assertRaises(ValueError, can.Notifier, bus, [], 0.1)
            
            notifier.stop()

    def test_double_restart_warning(self):
        with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
            with can.Notifier(bus, [], 0.1) as notifier:
                # Attempting to restart an already running notifier should warn
                with self.assertRaises(RuntimeWarning):
                    notifier.restart()

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

    def test_asyncio_notifier_restart(self):
        async def run_it():
            with can.Bus("test", interface="virtual", receive_own_messages=True) as bus:
                reader = can.AsyncBufferedReader()
                notifier = can.Notifier(
                    bus, [reader], 0.1, loop=asyncio.get_running_loop()
                )
                
                notifier.stop()
                
                # In some cases, creating a new listener is the safest path for a restart
                new_reader = can.AsyncBufferedReader()
                notifier.listeners = [new_reader] 
                
                notifier.restart()
                
                # Small yield to let the selector register the FD
                await asyncio.sleep(0.1)
                
                bus.send(can.Message(arbitration_id=0x123))
                
                recv_msg = await asyncio.wait_for(new_reader.get_message(), 1.5)
                
                self.assertIsNotNone(recv_msg)
                self.assertEqual(recv_msg.arbitration_id, 0x123)
                
                notifier.stop()

        asyncio.run(run_it())


if __name__ == "__main__":
    unittest.main()

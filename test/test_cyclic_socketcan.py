#!/usr/bin/env python

"""
This module tests multiple message cyclic send tasks.
"""
import unittest

import time
import can

from .config import TEST_INTERFACE_SOCKETCAN


@unittest.skipUnless(TEST_INTERFACE_SOCKETCAN, "skip testing of socketcan")
class CyclicSocketCan(unittest.TestCase):
    BITRATE = 500000
    TIMEOUT = 0.1

    INTERFACE_1 = "socketcan"
    CHANNEL_1 = "vcan0"
    INTERFACE_2 = "socketcan"
    CHANNEL_2 = "vcan0"

    PERIOD = 1.0

    DELTA = 0.01

    def _find_start_index(self, tx_messages, message):
        """
        :param tx_messages:
            The list of messages that were passed to the periodic backend
        :param message:
            The message whose data we wish to match and align to

        :returns: start index in the tx_messages
        """
        start_index = -1
        for index, tx_message in enumerate(tx_messages):
            if tx_message.data == message.data:
                start_index = index
                break
        return start_index

    def setUp(self):
        self._send_bus = can.Bus(
            interface=self.INTERFACE_1, channel=self.CHANNEL_1, bitrate=self.BITRATE
        )
        self._recv_bus = can.Bus(
            interface=self.INTERFACE_2, channel=self.CHANNEL_2, bitrate=self.BITRATE
        )

    def tearDown(self):
        self._send_bus.shutdown()
        self._recv_bus.shutdown()

    def test_cyclic_initializer_list(self):
        messages = []
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
                is_extended_id=False,
            )
        )

        task = self._send_bus.send_periodic(messages, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        results = []
        for _ in range(len(messages) * 2):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results.append(result)

        task.stop()

        # Find starting index for each
        start_index = self._find_start_index(messages, results[0])
        self.assertTrue(start_index != -1)

        # Now go through the partitioned results and assert that they're equal
        for rx_index, rx_message in enumerate(results):
            tx_message = messages[start_index]

            self.assertIsNotNone(rx_message)
            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            start_index = (start_index + 1) % len(messages)

    def test_cyclic_initializer_tuple(self):
        messages = []
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
                is_extended_id=False,
            )
        )
        messages = tuple(messages)

        self.assertIsInstance(messages, tuple)

        task = self._send_bus.send_periodic(messages, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        results = []
        for _ in range(len(messages) * 2):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results.append(result)

        task.stop()

        # Find starting index for each
        start_index = self._find_start_index(messages, results[0])
        self.assertTrue(start_index != -1)

        # Now go through the partitioned results and assert that they're equal
        for rx_index, rx_message in enumerate(results):
            tx_message = messages[start_index]

            self.assertIsNotNone(rx_message)
            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            start_index = (start_index + 1) % len(messages)

    def test_cyclic_initializer_message(self):
        message = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )

        task = self._send_bus.send_periodic(message, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.CyclicSendTaskABC)

        # Take advantage of kernel's queueing mechanisms
        time.sleep(4 * self.PERIOD)
        task.stop()

        for _ in range(4):
            tx_message = message
            rx_message = self._recv_bus.recv(self.TIMEOUT)

            self.assertIsNotNone(rx_message)
            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

    def test_cyclic_initializer_invalid_none(self):
        with self.assertRaises(ValueError):
            task = self._send_bus.send_periodic(None, self.PERIOD)

    def test_cyclic_initializer_invalid_empty_list(self):
        with self.assertRaises(ValueError):
            task = self._send_bus.send_periodic([], self.PERIOD)

    def test_cyclic_initializer_different_arbitration_ids(self):
        messages = []
        messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
                is_extended_id=False,
            )
        )
        messages.append(
            can.Message(
                arbitration_id=0x3E1,
                data=[0xEE, 0xEE, 0xEE, 0xEE, 0xEE, 0xEE],
                is_extended_id=False,
            )
        )
        with self.assertRaises(ValueError):
            task = self._send_bus.send_periodic(messages, self.PERIOD)

    def test_start_already_started_task(self):
        messages_a = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )

        task_a = self._send_bus.send_periodic(messages_a, self.PERIOD)
        time.sleep(0.1)

        # Try to start it again, task_id is not incremented in this case
        with self.assertRaises(can.CanOperationError) as ctx:
            task_a.start()
        self.assertEqual(
            "A periodic task for task ID 1 is already in progress by the SocketCAN Linux layer",
            str(ctx.exception),
        )

        task_a.stop()

    def test_create_same_id(self):
        messages_a = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )

        messages_b = can.Message(
            arbitration_id=0x401,
            data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
            is_extended_id=False,
        )

        task_a = self._send_bus.send_periodic(messages_a, self.PERIOD)
        self.assertIsInstance(task_a, can.broadcastmanager.CyclicSendTaskABC)
        task_b = self._send_bus.send_periodic(messages_b, self.PERIOD)
        self.assertIsInstance(task_b, can.broadcastmanager.CyclicSendTaskABC)

        time.sleep(self.PERIOD * 4)

        task_a.stop()
        task_b.stop()

        msgs = []
        for _ in range(4):
            msg = self._recv_bus.recv(self.PERIOD * 2)
            self.assertIsNotNone(msg)

            msgs.append(msg)

        self.assertTrue(len(msgs) >= 4)

        # Both messages should be recevied on the bus,
        # even with the same arbitration id
        msg_a_data_present = msg_b_data_present = False
        for rx_message in msgs:
            self.assertTrue(
                rx_message.arbitration_id
                == messages_a.arbitration_id
                == messages_b.arbitration_id
            )
            if rx_message.data == messages_a.data:
                msg_a_data_present = True
            if rx_message.data == messages_b.data:
                msg_b_data_present = True

        self.assertTrue(msg_a_data_present)
        self.assertTrue(msg_b_data_present)

    def test_modify_data_list(self):
        messages_odd = []
        messages_odd.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
                is_extended_id=False,
            )
        )
        messages_odd.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
                is_extended_id=False,
            )
        )
        messages_odd.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x55, 0x55, 0x55, 0x55, 0x55, 0x55],
                is_extended_id=False,
            )
        )
        messages_even = []
        messages_even.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
                is_extended_id=False,
            )
        )
        messages_even.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x44, 0x44, 0x44, 0x44, 0x44, 0x44],
                is_extended_id=False,
            )
        )
        messages_even.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x66, 0x66, 0x66, 0x66, 0x66, 0x66],
                is_extended_id=False,
            )
        )

        task = self._send_bus.send_periodic(messages_odd, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.ModifiableCyclicTaskABC)

        results_odd = []
        results_even = []
        for _ in range(len(messages_odd) * 2):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results_odd.append(result)

        task.modify_data(messages_even)
        for _ in range(len(messages_even) * 2):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results_even.append(result)

        task.stop()

        # Make sure we received some messages
        self.assertTrue(len(results_even) != 0)
        self.assertTrue(len(results_odd) != 0)

        # Find starting index for each
        start_index_even = self._find_start_index(messages_even, results_even[0])
        self.assertTrue(start_index_even != -1)

        start_index_odd = self._find_start_index(messages_odd, results_odd[0])
        self.assertTrue(start_index_odd != -1)

        # Now go through the partitioned results and assert that they're equal
        for rx_index, rx_message in enumerate(results_even):
            tx_message = messages_even[start_index_even]

            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            start_index_even = (start_index_even + 1) % len(messages_even)

            if rx_index != 0:
                prev_rx_message = results_even[rx_index - 1]
                # Assert timestamps are within the expected period
                self.assertTrue(
                    abs(
                        (rx_message.timestamp - prev_rx_message.timestamp) - self.PERIOD
                    )
                    <= self.DELTA
                )

        for rx_index, rx_message in enumerate(results_odd):
            tx_message = messages_odd[start_index_odd]

            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            start_index_odd = (start_index_odd + 1) % len(messages_odd)

            if rx_index != 0:
                prev_rx_message = results_odd[rx_index - 1]
                # Assert timestamps are within the expected period
                self.assertTrue(
                    abs(
                        (rx_message.timestamp - prev_rx_message.timestamp) - self.PERIOD
                    )
                    <= self.DELTA
                )

    def test_modify_data_message(self):
        message_odd = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
        message_even = can.Message(
            arbitration_id=0x401,
            data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
            is_extended_id=False,
        )
        task = self._send_bus.send_periodic(message_odd, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.ModifiableCyclicTaskABC)

        results_odd = []
        results_even = []
        for _ in range(1 * 4):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results_odd.append(result)

        task.modify_data(message_even)
        for _ in range(1 * 4):
            result = self._recv_bus.recv(self.PERIOD * 2)
            if result:
                results_even.append(result)

        task.stop()

        # Now go through the partitioned results and assert that they're equal
        for rx_index, rx_message in enumerate(results_even):
            tx_message = message_even

            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            if rx_index != 0:
                prev_rx_message = results_even[rx_index - 1]
                # Assert timestamps are within the expected period
                self.assertTrue(
                    abs(
                        (rx_message.timestamp - prev_rx_message.timestamp) - self.PERIOD
                    )
                    <= self.DELTA
                )

        for rx_index, rx_message in enumerate(results_odd):
            tx_message = message_odd

            self.assertEqual(tx_message.arbitration_id, rx_message.arbitration_id)
            self.assertEqual(tx_message.dlc, rx_message.dlc)
            self.assertEqual(tx_message.data, rx_message.data)
            self.assertEqual(tx_message.is_extended_id, rx_message.is_extended_id)
            self.assertEqual(tx_message.is_remote_frame, rx_message.is_remote_frame)
            self.assertEqual(tx_message.is_error_frame, rx_message.is_error_frame)
            self.assertEqual(tx_message.is_fd, rx_message.is_fd)

            if rx_index != 0:
                prev_rx_message = results_odd[rx_index - 1]
                # Assert timestamps are within the expected period
                self.assertTrue(
                    abs(
                        (rx_message.timestamp - prev_rx_message.timestamp) - self.PERIOD
                    )
                    <= self.DELTA
                )

    def test_modify_data_invalid(self):
        message = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
        task = self._send_bus.send_periodic(message, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.ModifiableCyclicTaskABC)

        time.sleep(2 * self.PERIOD)

        with self.assertRaises(ValueError):
            task.modify_data(None)

    def test_modify_data_unequal_lengths(self):
        message = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
        new_messages = []
        new_messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
                is_extended_id=False,
            )
        )
        new_messages.append(
            can.Message(
                arbitration_id=0x401,
                data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
                is_extended_id=False,
            )
        )

        task = self._send_bus.send_periodic(message, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.ModifiableCyclicTaskABC)

        time.sleep(2 * self.PERIOD)

        with self.assertRaises(ValueError):
            task.modify_data(new_messages)

    def test_modify_data_different_arbitration_id_than_original(self):
        old_message = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
        new_message = can.Message(
            arbitration_id=0x3E1,
            data=[0xEE, 0xEE, 0xEE, 0xEE, 0xEE, 0xEE],
            is_extended_id=False,
        )

        task = self._send_bus.send_periodic(old_message, self.PERIOD)
        self.assertIsInstance(task, can.broadcastmanager.ModifiableCyclicTaskABC)

        time.sleep(2 * self.PERIOD)

        with self.assertRaises(ValueError):
            task.modify_data(new_message)

    def test_stop_all_periodic_tasks_and_remove_task(self):
        message_a = can.Message(
            arbitration_id=0x401,
            data=[0x11, 0x11, 0x11, 0x11, 0x11, 0x11],
            is_extended_id=False,
        )
        message_b = can.Message(
            arbitration_id=0x402,
            data=[0x22, 0x22, 0x22, 0x22, 0x22, 0x22],
            is_extended_id=False,
        )
        message_c = can.Message(
            arbitration_id=0x403,
            data=[0x33, 0x33, 0x33, 0x33, 0x33, 0x33],
            is_extended_id=False,
        )

        # Start Tasks
        task_a = self._send_bus.send_periodic(message_a, self.PERIOD)
        task_b = self._send_bus.send_periodic(message_b, self.PERIOD)
        task_c = self._send_bus.send_periodic(message_c, self.PERIOD)

        self.assertIsInstance(task_a, can.broadcastmanager.ModifiableCyclicTaskABC)
        self.assertIsInstance(task_b, can.broadcastmanager.ModifiableCyclicTaskABC)
        self.assertIsInstance(task_c, can.broadcastmanager.ModifiableCyclicTaskABC)

        for _ in range(6):
            _ = self._recv_bus.recv(self.PERIOD)

        # Stop all tasks and delete
        self._send_bus.stop_all_periodic_tasks(remove_tasks=True)

        # Now wait for a few periods, after which we should definitely not
        # receive any CAN messages
        time.sleep(4 * self.PERIOD)

        # If we successfully deleted everything, then we will eventually read
        # 0 messages.
        successfully_stopped = False
        for _ in range(6):
            rx_message = self._recv_bus.recv(self.PERIOD)

            if rx_message is None:
                successfully_stopped = True
                break
        self.assertTrue(successfully_stopped, "Still received messages after stopping")

        # None of the tasks should still be associated with the bus
        self.assertEqual(0, len(self._send_bus._periodic_tasks))


if __name__ == "__main__":
    unittest.main()

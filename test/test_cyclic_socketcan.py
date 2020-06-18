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

    def test_create_same_id_raises_exception(self):
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

        task_a = self._send_bus.send_periodic(messages_a, 1)
        self.assertIsInstance(task_a, can.broadcastmanager.CyclicSendTaskABC)

        # The second one raises a ValueError when we attempt to create a new
        # Task, since it has the same arbitration ID.
        with self.assertRaises(ValueError):
            task_b = self._send_bus.send_periodic(messages_b, 1)

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


if __name__ == "__main__":
    unittest.main()

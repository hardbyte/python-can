# coding: utf-8
# TODO documentation
"""
Name:        interface_test.py
Purpose:     Generic tests for the bus interfaces.
             These tests should cover all functions offered by the bus interface.

Copyright:   2018 Boris Wenzlaff

This file is part of python-can <https://github.com/hardbyte/python-can/>.

python-can is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

python-can is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with python-can. If not, see <http://www.gnu.org/licenses/>.
"""

from can import Message
from can import CanError
from can.interfaces.serial.slcan import SlcanBus

sleep_time_rx_tx = None


def skip_interface(interface_class, comment=None):
    """
    Decorator to skip tests.
    :param interface_class: Skip test for this class.
    :param comment: Reason why skipped.
    """
    def deco(f):
        def wrapper(self, *args, **kwargs):
            if isinstance(self.bus, interface_class):
                self.skipTest(str(comment))
            else:
                f(self, *args, **kwargs)
        return wrapper
    return deco


class GenericInterfaceTest(object):
    __MAX_TIMESTAMP = 0xFFFFFFFF / 1000

    def test_rx_tx_min_max_data(self):
        """
        Tests the transfer from 0x00 to 0xFF for a 1 byte payload
        """
        for b in range(0, 255):
            msg = Message(data=[b])
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertEqual(msg, msg_receive)

    def test_rx_tx_min_max_dlc(self):
        """
        Tests the transfer from a 1 - 8 byte payload
        """
        payload = bytearray()
        for b in range(1, 9):
            payload.append(0)
            msg = Message(data=payload)
            self.bus.send(msg)
            msg_receive = self.bus.recv()
            self.assertEqual(msg, msg_receive)

    def test_rx_tx_data_none(self):
        """
        Tests the transfer without payload
        """
        msg = Message(data=None)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_min_id(self):
        """
        Tests the transfer with the lowest arbitration id
        """
        msg = Message(arbitration_id=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    def test_rx_tx_max_id(self):
        """
        Tests the transfer with the highest arbitration id
        """
        msg = Message(arbitration_id=536870911)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_tx_max_timestamp(self):
        """
        Tests the transfer with the highest possible timestamp
        """
        msg = Message(timestamp=self.__MAX_TIMESTAMP)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_tx_max_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (max + 1)
        """
        msg = Message(timestamp=self.__MAX_TIMESTAMP + 1)
        self.assertRaises(ValueError, self.bus.send, msg)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_tx_min_timestamp(self):
        """
        Tests the transfer with the lowest possible timestamp
        """
        msg = Message(timestamp=0)
        self.bus.send(msg)
        msg_receive = self.bus.recv()
        self.assertEqual(msg, msg_receive)
        self.assertEqual(msg.timestamp, msg_receive.timestamp)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_tx_min_timestamp_error(self):
        """
        Tests for an exception with an out of range timestamp (min - 1)
        """
        msg = Message(timestamp=-1)
        self.assertRaises(ValueError, self.bus.send, msg)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_timeout_default(self):
        """
        Tests for CanError for default timeout on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        with self.assertRaises(CanError):
            self.bus.send(Message(timestamp=1))

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_non_timeout_default(self):
        """
        Tests for non CanError for default timeout on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.09
        self.bus.send(Message(timestamp=1))

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_timeout_param(self):
        """
        Tests for CanError on send with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 3
        with self.assertRaises(CanError):
            self.bus.send(Message(timestamp=1), 2)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_non_timeout_param(self):
        """
        Tests for non CanError on send with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 1.9
        self.bus.send(Message(timestamp=1), 2)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_tx_reset_timeout(self):
        """
        Tests reset of the timeout after a timeout is set with an parameter on send
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(Message(timestamp=1), 0.12)
        with self.assertRaises(CanError):
            self.bus.send(Message(timestamp=1))

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_timeout_default(self):
        """
        Tests for default timeout on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        self.bus.send(Message(timestamp=1), 100)
        self.assertIsNone(self.bus.recv())

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_non_timeout_default(self):
        """
        Tests for non timeout on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.09
        msg = Message(timestamp=1)
        self.bus.send(msg, 100)
        self.assertEqual(self.bus.recv(), msg)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_timeout_param(self):
        """
        Tests for timeout on receive with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 3
        self.bus.send(Message(timestamp=1), 100)
        self.assertIsNone(self.bus.recv(timeout=2))

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_non_timeout_param(self):
        """
        Tests for non timeout on receive with timeout parameter
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 1.9
        msg = Message(timestamp=1)
        self.bus.send(msg, 100)
        self.assertEqual(self.bus.recv(2), msg)

    @skip_interface(SlcanBus, 'function not implemented')
    def test_rx_reset_timeout(self):
        """
        Tests reset of the timeout after a timeout is set with an parameter on receive
        """
        global sleep_time_rx_tx
        sleep_time_rx_tx = 0.11
        msg = Message(timestamp=1)
        self.bus.send(msg, 100)
        self.bus.recv(2)
        self.bus.send(msg, 100)
        self.assertIsNone(self.bus.recv())

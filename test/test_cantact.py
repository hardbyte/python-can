#!/usr/bin/env python

"""
Tests for CANtact interfaces
"""

import unittest

import can
from can.interfaces import cantact


class CantactTest(unittest.TestCase):
    def test_bus_creation(self):
        bus = can.Bus(channel=0, interface="cantact", _testing=True)
        self.assertIsInstance(bus, cantact.CantactBus)
        self.assertEqual(bus.protocol, can.CanProtocol.CAN_20)

        cantact.MockInterface.set_bitrate.assert_called()
        cantact.MockInterface.set_bit_timing.assert_not_called()
        cantact.MockInterface.set_enabled.assert_called()
        cantact.MockInterface.set_monitor.assert_called()
        cantact.MockInterface.start.assert_called()

    def test_bus_creation_bittiming(self):
        cantact.MockInterface.set_bitrate.reset_mock()

        bt = can.BitTiming(f_clock=24_000_000, brp=3, tseg1=13, tseg2=2, sjw=1)
        bus = can.Bus(channel=0, interface="cantact", timing=bt, _testing=True)

        self.assertIsInstance(bus, cantact.CantactBus)
        self.assertEqual(bus.protocol, can.CanProtocol.CAN_20)

        cantact.MockInterface.set_bitrate.assert_not_called()
        cantact.MockInterface.set_bit_timing.assert_called()
        cantact.MockInterface.set_enabled.assert_called()
        cantact.MockInterface.set_monitor.assert_called()
        cantact.MockInterface.start.assert_called()

    def test_transmit(self):
        bus = can.Bus(channel=0, interface="cantact", _testing=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        bus.send(msg)
        cantact.MockInterface.send.assert_called()

    def test_recv(self):
        bus = can.Bus(channel=0, interface="cantact", _testing=True)
        frame = bus.recv(timeout=0.5)
        cantact.MockInterface.recv.assert_called()
        self.assertIsInstance(frame, can.Message)

    def test_recv_timeout(self):
        bus = can.Bus(channel=0, interface="cantact", _testing=True)
        frame = bus.recv(timeout=0.0)
        cantact.MockInterface.recv.assert_called()
        self.assertIsNone(frame)

    def test_listen_only(self):
        """
        Test Scope:
            Listen-only mode of the CANtact interface.
        Preconditions:
            A mocked CANtact device.
        Events:
            Create a listen-only bus and try to send a message.
        Evaluate:
            Monitor mode is switched on, send raises CanOperationError and no
            frame is passed to the device.
        """
        cantact.MockInterface.send.reset_mock()
        bus = can.Bus(channel=0, interface="cantact", listen_only=True, _testing=True)

        cantact.MockInterface.set_monitor.assert_called_with(0, True)
        with self.assertRaises(can.CanOperationError):
            bus.send(can.Message(arbitration_id=0x123))
        cantact.MockInterface.send.assert_not_called()

    def test_monitor_deprecated(self):
        """
        Test Scope:
            The deprecated monitor argument of the CANtact interface.
        Preconditions:
            A mocked CANtact device.
        Events:
            Create a bus with monitor set to True.
        Evaluate:
            A DeprecationWarning is emitted and monitor mode is switched on.
        """
        cantact.MockInterface.set_monitor.reset_mock()
        with self.assertWarns(DeprecationWarning):
            can.Bus(channel=0, interface="cantact", monitor=True, _testing=True)

        cantact.MockInterface.set_monitor.assert_called_with(0, True)

    def test_shutdown(self):
        bus = can.Bus(channel=0, interface="cantact", _testing=True)
        bus.shutdown()
        cantact.MockInterface.stop.assert_called()

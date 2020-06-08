#!/usr/bin/env python
# coding: utf-8

"""
Tests for CANtact interfaces
"""

import time
import logging
import unittest
from unittest.mock import Mock, patch

import pytest

import can
from can.interfaces import cantact


class CantactTest(unittest.TestCase):
    def test_bus_creation(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        self.assertIsInstance(bus, cantact.CantactBus)
        cantact.MockInterface.set_bitrate.assert_called()
        cantact.MockInterface.set_enabled.assert_called()
        cantact.MockInterface.set_monitor.assert_called()
        cantact.MockInterface.start.assert_called()

    def test_transmit(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        bus.send(msg)
        cantact.MockInterface.send.assert_called()

    def test_recv(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        frame = bus.recv(timeout=0.5)
        cantact.MockInterface.recv.assert_called()
        self.assertIsInstance(frame, can.Message)

    def test_recv_timeout(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        frame = bus.recv(timeout=0.0)
        cantact.MockInterface.recv.assert_called()
        self.assertIsNone(frame)

    def test_shutdown(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        bus.shutdown()
        cantact.MockInterface.stop.assert_called()

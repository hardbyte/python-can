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
import cantact as cantactdrv
from can.interfaces import cantact


def recv(timeout):
    if timeout > 0:
        frame = {}
        frame["id"] = 0x123
        frame["extended"] = False
        frame["timestamp"] = time.time()
        frame["rtr"] = False
        frame["dlc"] = 8
        frame["data"] = [1, 2, 3, 4, 5, 6, 7, 8]
        frame["channel"] = 0
        return frame
    else:
        # simulate timeout when timeout = 0
        return None


"""
Mock methods for CANtact library to allow test without hardware
"""


class MockInterface:
    start = Mock()
    set_bitrate = Mock()
    set_enabled = Mock()
    set_monitor = Mock()
    start = Mock()
    stop = Mock()
    send = Mock()
    recv = Mock(side_effect=recv)
    channel_count = Mock(return_value=1)


class CantactTest(unittest.TestCase):
    def setUp(self):
        cantactdrv.Interface = MockInterface

    def test_bus_creation(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        self.assertIsInstance(bus, cantact.CantactBus)
        cantactdrv.Interface.set_bitrate.assert_called()
        cantactdrv.Interface.set_enabled.assert_called()
        cantactdrv.Interface.set_monitor.assert_called()
        cantactdrv.Interface.start.assert_called()

    def test_transmit(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        bus.send(msg)
        cantactdrv.Interface.send.assert_called()

    def test_recv(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        frame = bus.recv(timeout=0.5)
        cantactdrv.Interface.recv.assert_called()
        self.assertIsInstance(frame, can.Message)

    def test_recv_timeout(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        frame = bus.recv(timeout=0.0)
        cantactdrv.Interface.recv.assert_called()
        self.assertIsNone(frame)

    def test_shutdown(self):
        bus = can.Bus(channel=0, bustype="cantact", _testing=True)
        bus.shutdown()
        cantactdrv.Interface.stop.assert_called()

    def test_available_configs(self):
        configs = cantact.CantactBus._detect_available_configs()
        expected = [{"interface": "cantact", "channel": "ch:0"}]
        self.assertListEqual(configs, expected)

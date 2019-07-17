#!/usr/bin/env python
# coding: utf-8

"""
"""

import ctypes
import time
import logging
import unittest
from unittest.mock import Mock, MagicMock, patch

import pytest

import can
from can.interfaces.vector import canlib


class TestVectorBus(unittest.TestCase):
    def setUp(self) -> None:
        can.interfaces.vector.canlib.vxlapi = Mock()
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver = Mock()
        can.interfaces.vector.canlib.vxlapi.XLportHandle = Mock()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig = Mock()
        can.interfaces.vector.canlib.vxlapi.xlOpenPort = Mock()
        can.interfaces.vector.canlib.vxlapi.xlGetChannelIndex = Mock(return_value=0)
        can.interfaces.vector.canlib.vxlapi.XLuint64 = Mock(return_value=ctypes.c_int64(0))
        can.interfaces.vector.canlib.vxlapi.xlCanReceive = Mock(return_value=0)
        can.interfaces.vector.canlib.vxlapi.xlReceive = Mock(return_value=0)
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration = Mock()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate = Mock()
        can.interfaces.vector.canlib.vxlapi.XL_CAN_EXT_MSG_ID = 0x80000000
        can.interfaces.vector.canlib.vxlapi.XLevent = MagicMock()
        can.interfaces.vector.canlib.vxlapi.XLcanTxEvent = MagicMock()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit = Mock()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx = Mock()
        can.interfaces.vector.canlib.vxlapi.xlCanFlushTransmitQueue = Mock()
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel = Mock()
        can.interfaces.vector.canlib.vxlapi.xlClosePort = Mock()
        can.interfaces.vector.canlib.vxlapi.xlCloseDriver = Mock()
        can.interfaces.vector.canlib.vxlapi.xlActivateChannel = Mock()
        self.bus = None

    def tearDown(self) -> None:
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def test_bus_creation(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector')
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()

    def test_bus_creation_bitrate(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector', bitrate='500000')
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_called()

    def test_bus_creation_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector', fd=True)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()

    def test_bus_creation_fd_bitrate_timings(self) -> None:
        self.bus = can.Bus(channel=0,
                           bustype='vector',
                           fd=True,
                           bitrate='500000',
                           data_bitrate='2000000',
                           sjwAbr=10,
                           tseg1Abr=11,
                           tseg2Abr=12,
                           sjwDbr=13,
                           tseg1Dbr=14,
                           tseg2Dbr=15)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()
        self.assertEqual(self.bus.canFdConf.arbitrationBitRate.value, 500000)
        self.assertEqual(self.bus.canFdConf.dataBitRate.value, 2000000)
        self.assertEqual(self.bus.canFdConf.sjwAbr.value, 10)
        self.assertEqual(self.bus.canFdConf.tseg1Abr.value, 11)
        self.assertEqual(self.bus.canFdConf.tseg2Abr.value, 12)
        self.assertEqual(self.bus.canFdConf.sjwDbr.value, 13)
        self.assertEqual(self.bus.canFdConf.tseg1Dbr.value, 14)
        self.assertEqual(self.bus.canFdConf.tseg2Dbr.value, 15)

    def test_receive(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector')
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.vxlapi.xlReceive.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanReceive.assert_not_called()

    def test_receive_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector', fd=True)
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.vxlapi.xlReceive.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanReceive.assert_called()

    def test_send(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector')
        msg = can.Message(arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True)
        self.bus.send(msg)
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx.assert_not_called()

    def test_send_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector', fd=True)
        msg = can.Message(arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True)
        self.bus.send(msg)
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx.assert_called()

    def test_flush_tx_buffer(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector')
        self.bus.flush_tx_buffer()
        can.interfaces.vector.canlib.vxlapi.xlCanFlushTransmitQueue.assert_called()

    def test_shutdown(self) -> None:
        self.bus = can.Bus(channel=0, bustype='vector')
        self.bus.shutdown()
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlClosePort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCloseDriver.assert_called()

    def test_reset(self):
        self.bus = can.Bus(channel=0, bustype='vector')
        self.bus.reset()
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlActivateChannel.assert_called()

if __name__ == "__main__":
    unittest.main()

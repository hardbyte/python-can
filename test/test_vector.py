#!/usr/bin/env python
# coding: utf-8

"""
Test for Vector Interface
"""

import ctypes
import time
import logging
import os
import unittest
from unittest.mock import Mock

import pytest

import can
from can.interfaces.vector import canlib, xldefine, xlclass


class TestVectorBus(unittest.TestCase):
    def setUp(self) -> None:
        # basic mock for XLDriver
        can.interfaces.vector.canlib.xldriver = Mock()

        # bus creation functions
        can.interfaces.vector.canlib.xldriver.xlOpenDriver = Mock()
        can.interfaces.vector.canlib.xldriver.xlGetApplConfig = Mock(
            side_effect=xlGetApplConfig
        )
        can.interfaces.vector.canlib.xldriver.xlGetChannelIndex = Mock(
            side_effect=xlGetChannelIndex
        )
        can.interfaces.vector.canlib.xldriver.xlOpenPort = Mock(side_effect=xlOpenPort)
        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration = Mock(
            return_value=0
        )
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelMode = Mock(return_value=0)
        can.interfaces.vector.canlib.xldriver.xlActivateChannel = Mock(return_value=0)
        can.interfaces.vector.canlib.xldriver.xlGetSyncTime = Mock(
            side_effect=xlGetSyncTime
        )
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelAcceptance = Mock(
            return_value=0
        )
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate = Mock(
            return_value=0
        )
        can.interfaces.vector.canlib.xldriver.xlSetNotification = Mock(
            side_effect=xlSetNotification
        )

        # bus deactivation functions
        can.interfaces.vector.canlib.xldriver.xlDeactivateChannel = Mock(return_value=0)
        can.interfaces.vector.canlib.xldriver.xlClosePort = Mock(return_value=0)
        can.interfaces.vector.canlib.xldriver.xlCloseDriver = Mock()

        # sender functions
        can.interfaces.vector.canlib.xldriver.xlCanTransmit = Mock(return_value=0)
        can.interfaces.vector.canlib.xldriver.xlCanTransmitEx = Mock(return_value=0)

        # various functions
        can.interfaces.vector.canlib.xldriver.xlCanFlushTransmitQueue = Mock()
        can.interfaces.vector.canlib.WaitForSingleObject = Mock()

        self.bus = None

    def tearDown(self) -> None:
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def test_bus_creation(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
        self.assertEqual(
            xlOpenPort_args[5], xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value
        )
        self.assertEqual(xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value)

        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()

    def test_bus_creation_bitrate(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", bitrate=200000, _testing=True)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
        self.assertEqual(
            xlOpenPort_args[5], xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value
        )
        self.assertEqual(xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value)

        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_called()
        xlCanSetChannelBitrate_args = can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.call_args[
            0
        ]
        self.assertEqual(xlCanSetChannelBitrate_args[2], 200000)

    def test_bus_creation_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
        self.assertEqual(
            xlOpenPort_args[5],
            xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
        )
        self.assertEqual(xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value)

        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()

    def test_bus_creation_fd_bitrate_timings(self) -> None:
        self.bus = can.Bus(
            channel=0,
            bustype="vector",
            fd=True,
            bitrate=500000,
            data_bitrate=2000000,
            sjwAbr=10,
            tseg1Abr=11,
            tseg2Abr=12,
            sjwDbr=13,
            tseg1Dbr=14,
            tseg2Dbr=15,
            _testing=True,
        )
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
        self.assertEqual(
            xlOpenPort_args[5],
            xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
        )
        self.assertEqual(xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value)

        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()

        xlCanFdSetConfiguration_args = can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.call_args[
            0
        ]
        canFdConf = xlCanFdSetConfiguration_args[2]
        self.assertEqual(canFdConf.arbitrationBitRate, 500000)
        self.assertEqual(canFdConf.dataBitRate, 2000000)
        self.assertEqual(canFdConf.sjwAbr, 10)
        self.assertEqual(canFdConf.tseg1Abr, 11)
        self.assertEqual(canFdConf.tseg2Abr, 12)
        self.assertEqual(canFdConf.sjwDbr, 13)
        self.assertEqual(canFdConf.tseg1Dbr, 14)
        self.assertEqual(canFdConf.tseg2Dbr, 15)

    def test_receive(self) -> None:
        can.interfaces.vector.canlib.xldriver.xlReceive = Mock(side_effect=xlReceive)
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()

    def test_receive_fd(self) -> None:
        can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(
            side_effect=xlCanReceive
        )
        self.bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
        can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()

    def test_receive_non_msg_event(self) -> None:
        can.interfaces.vector.canlib.xldriver.xlReceive = Mock(
            side_effect=xlReceive_chipstate
        )
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.bus.handle_can_event = Mock()
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()
        self.bus.handle_can_event.assert_called()

    def test_receive_fd_non_msg_event(self) -> None:
        can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(
            side_effect=xlCanReceive_chipstate
        )
        self.bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
        self.bus.handle_canfd_event = Mock()
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
        can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()
        self.bus.handle_canfd_event.assert_called()

    def test_send(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_not_called()

    def test_send_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_not_called()
        can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_called()

    def test_flush_tx_buffer(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.bus.flush_tx_buffer()
        can.interfaces.vector.canlib.xldriver.xlCanFlushTransmitQueue.assert_called()

    def test_shutdown(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.bus.shutdown()
        can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.xldriver.xlClosePort.assert_called()
        can.interfaces.vector.canlib.xldriver.xlCloseDriver.assert_called()

    def test_reset(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", _testing=True)
        self.bus.reset()
        can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.xldriver.xlActivateChannel.assert_called()

    def test_called_without_testing_argument(self) -> None:
        """This tests if an exception is thrown when we are not running on Windows."""
        if os.name != "nt":
            with self.assertRaises(OSError):
                # do not set the _testing argument, since it supresses the exception
                can.Bus(channel=0, bustype="vector")


def xlGetApplConfig(
    app_name_p: ctypes.c_char_p,
    app_channel: ctypes.c_uint,
    hw_type: ctypes.POINTER(ctypes.c_uint),
    hw_index: ctypes.POINTER(ctypes.c_uint),
    hw_channel: ctypes.POINTER(ctypes.c_uint),
    bus_type: ctypes.c_uint,
) -> int:
    hw_type.value = 1
    hw_channel.value = app_channel
    return 0


def xlGetChannelIndex(
    hw_type: ctypes.c_int, hw_index: ctypes.c_int, hw_channel: ctypes.c_int
) -> int:
    return hw_channel


def xlOpenPort(
    port_handle_p: ctypes.POINTER(xlclass.XLportHandle),
    app_name_p: ctypes.c_char_p,
    access_mask: xlclass.XLaccess,
    permission_mask_p: ctypes.POINTER(xlclass.XLaccess),
    rx_queue_size: ctypes.c_uint,
    xl_interface_version: ctypes.c_uint,
    bus_type: ctypes.c_uint,
) -> int:
    port_handle_p.value = 0
    return 0


def xlGetSyncTime(
    port_handle: xlclass.XLportHandle, time_p: ctypes.POINTER(xlclass.XLuint64)
) -> int:
    time_p.value = 544219859027581
    return 0


def xlSetNotification(
    port_handle: xlclass.XLportHandle,
    event_handle: ctypes.POINTER(xlclass.XLhandle),
    queue_level: ctypes.c_int,
) -> int:
    event_handle.value = 520
    return 0


def xlReceive(
    port_handle: xlclass.XLportHandle,
    event_count_p: ctypes.POINTER(ctypes.c_uint),
    event: ctypes.POINTER(xlclass.XLevent),
) -> int:
    event.tag = xldefine.XL_EventTags.XL_RECEIVE_MSG.value
    event.tagData.msg.id = 0x123
    event.tagData.msg.dlc = 8
    event.tagData.msg.flags = 0
    event.timeStamp = 0
    event.chanIndex = 0
    for idx, value in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        event.tagData.msg.data[idx] = value
    return 0


def xlCanReceive(
    port_handle: xlclass.XLportHandle, event: ctypes.POINTER(xlclass.XLcanRxEvent)
) -> int:
    event.tag = xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_RX_OK.value
    event.tagData.canRxOkMsg.canId = 0x123
    event.tagData.canRxOkMsg.dlc = 8
    event.tagData.canRxOkMsg.msgFlags = 0
    event.timeStamp = 0
    event.chanIndex = 0
    for idx, value in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        event.tagData.canRxOkMsg.data[idx] = value
    return 0


def xlReceive_chipstate(
    port_handle: xlclass.XLportHandle,
    event_count_p: ctypes.POINTER(ctypes.c_uint),
    event: ctypes.POINTER(xlclass.XLevent),
) -> int:
    event.tag = xldefine.XL_EventTags.XL_CHIP_STATE.value
    event.tagData.chipState.busStatus = 8
    event.tagData.chipState.rxErrorCounter = 0
    event.tagData.chipState.txErrorCounter = 0
    event.timeStamp = 0
    event.chanIndex = 2
    return 0


def xlCanReceive_chipstate(
    port_handle: xlclass.XLportHandle, event: ctypes.POINTER(xlclass.XLcanRxEvent)
) -> int:
    event.tag = xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_CHIP_STATE.value
    event.tagData.canChipState.busStatus = 8
    event.tagData.canChipState.rxErrorCounter = 0
    event.tagData.canChipState.txErrorCounter = 0
    event.timeStamp = 0
    event.chanIndex = 2
    return 0


if __name__ == "__main__":
    unittest.main()

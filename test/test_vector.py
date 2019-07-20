#!/usr/bin/env python
# coding: utf-8

"""
"""

import ctypes
import time
import logging
import unittest
from unittest.mock import Mock

import pytest

import can
from can.interfaces.vector import canlib, vxlapi


class TestVectorBus(unittest.TestCase):
    def setUp(self) -> None:
        # bus creation functions
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver = Mock()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig = Mock(
            side_effect=xlGetApplConfig
        )
        can.interfaces.vector.canlib.vxlapi.xlGetChannelIndex = Mock(
            side_effect=xlGetChannelIndex
        )
        can.interfaces.vector.canlib.vxlapi.xlOpenPort = Mock(side_effect=xlOpenPort)
        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration = Mock(
            side_effect=xlCanFdSetConfiguration
        )
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelMode = Mock(
            side_effect=xlCanSetChannelMode
        )
        can.interfaces.vector.canlib.vxlapi.xlActivateChannel = Mock(
            side_effect=xlActivateChannel
        )
        can.interfaces.vector.canlib.vxlapi.xlGetSyncTime = Mock(
            side_effect=xlGetSyncTime
        )
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelAcceptance = Mock(
            side_effect=xlCanSetChannelAcceptance
        )
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate = Mock(
            side_effect=xlCanSetChannelBitrate
        )

        # bus deactivation functions
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel = Mock(
            side_effect=xlDeactivateChannel
        )
        can.interfaces.vector.canlib.vxlapi.xlClosePort = Mock(side_effect=xlClosePort)
        can.interfaces.vector.canlib.vxlapi.xlCloseDriver = Mock()

        # receiver functions
        can.interfaces.vector.canlib.vxlapi.xlReceive = Mock(side_effect=xlReceive)
        can.interfaces.vector.canlib.vxlapi.xlCanReceive = Mock(
            side_effect=xlCanReceive
        )

        # sender functions
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit = Mock(
            side_effect=xlCanTransmit
        )
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx = Mock(
            side_effect=xlCanTransmitEx
        )

        # various functions
        can.interfaces.vector.canlib.vxlapi.xlCanFlushTransmitQueue = Mock()
        can.interfaces.vector.canlib.WaitForSingleObject = Mock()

        self.bus = None

    def tearDown(self) -> None:
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def test_bus_creation(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector")
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.vxlapi.xlOpenPort.call_args[0]
        self.assertEqual(xlOpenPort_args[5], vxlapi.XL_INTERFACE_VERSION)
        self.assertEqual(xlOpenPort_args[6], vxlapi.XL_BUS_TYPE_CAN)

        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()

    def test_bus_creation_bitrate(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", bitrate=200000)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.vxlapi.xlOpenPort.call_args[0]
        self.assertEqual(xlOpenPort_args[5], vxlapi.XL_INTERFACE_VERSION)
        self.assertEqual(xlOpenPort_args[6], vxlapi.XL_BUS_TYPE_CAN)

        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_called()
        xlCanSetChannelBitrate_args = can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.call_args[
            0
        ]
        self.assertEqual(xlCanSetChannelBitrate_args[2], 200000)

    def test_bus_creation_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", fd=True)
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.vxlapi.xlOpenPort.call_args[0]
        self.assertEqual(xlOpenPort_args[5], vxlapi.XL_INTERFACE_VERSION_V4)
        self.assertEqual(xlOpenPort_args[6], vxlapi.XL_BUS_TYPE_CAN)

        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()

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
        )
        self.assertIsInstance(self.bus, canlib.VectorBus)
        can.interfaces.vector.canlib.vxlapi.xlOpenDriver.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlGetApplConfig.assert_called()

        can.interfaces.vector.canlib.vxlapi.xlOpenPort.assert_called()
        xlOpenPort_args = can.interfaces.vector.canlib.vxlapi.xlOpenPort.call_args[0]
        self.assertEqual(xlOpenPort_args[5], vxlapi.XL_INTERFACE_VERSION_V4)
        self.assertEqual(xlOpenPort_args[6], vxlapi.XL_BUS_TYPE_CAN)

        can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanSetChannelBitrate.assert_not_called()

        xlCanFdSetConfiguration_args = can.interfaces.vector.canlib.vxlapi.xlCanFdSetConfiguration.call_args[
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
        self.bus = can.Bus(channel=0, bustype="vector")
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.vxlapi.xlReceive.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanReceive.assert_not_called()

    def test_receive_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", fd=True)
        self.bus.recv(timeout=0.05)
        can.interfaces.vector.canlib.vxlapi.xlReceive.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanReceive.assert_called()

    def test_send(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector")
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx.assert_not_called()

    def test_send_fd(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector", fd=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        can.interfaces.vector.canlib.vxlapi.xlCanTransmit.assert_not_called()
        can.interfaces.vector.canlib.vxlapi.xlCanTransmitEx.assert_called()

    def test_flush_tx_buffer(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector")
        self.bus.flush_tx_buffer()
        can.interfaces.vector.canlib.vxlapi.xlCanFlushTransmitQueue.assert_called()

    def test_shutdown(self) -> None:
        self.bus = can.Bus(channel=0, bustype="vector")
        self.bus.shutdown()
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlClosePort.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlCloseDriver.assert_called()

    def test_reset(self):
        self.bus = can.Bus(channel=0, bustype="vector")
        self.bus.reset()
        can.interfaces.vector.canlib.vxlapi.xlDeactivateChannel.assert_called()
        can.interfaces.vector.canlib.vxlapi.xlActivateChannel.assert_called()


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
    port_handle_p: ctypes.POINTER(vxlapi.XLportHandle),
    app_name_p: ctypes.c_char_p,
    access_mask: vxlapi.XLaccess,
    permission_mask_p: ctypes.POINTER(vxlapi.XLaccess),
    rx_queue_size: ctypes.c_uint,
    xl_interface_version: ctypes.c_uint,
    bus_type: ctypes.c_uint,
) -> int:
    port_handle_p.value = 0
    return 0


def xlCanFdSetConfiguration(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    can_fd_conf_p: ctypes.POINTER(vxlapi.XLcanFdConf),
) -> int:
    return 0


def xlCanSetChannelMode(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    tx: ctypes.c_int,
    txrq: ctypes.c_int,
) -> int:
    return 0


def xlActivateChannel(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    bus_type: ctypes.c_uint,
    flags: ctypes.c_uint,
) -> int:
    return 0


def xlGetSyncTime(
    port_handle: vxlapi.XLportHandle, time_p: ctypes.POINTER(vxlapi.XLuint64)
) -> int:
    time_p.value = 544219859027581
    return 0


def xlCanSetChannelAcceptance(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    code: ctypes.c_ulong,
    mask: ctypes.c_ulong,
    id_range: ctypes.c_uint,
) -> int:
    return 0


def xlCanSetChannelBitrate(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    bitrate: ctypes.c_ulong,
) -> int:
    return 0


def xlDeactivateChannel(
    port_handle: vxlapi.XLportHandle, access_mask: vxlapi.XLaccess
) -> int:
    return 0


def xlClosePort(port_handle: vxlapi.XLportHandle,) -> int:
    return 0


def xlReceive(
    port_handle: vxlapi.XLportHandle,
    event_count_p: ctypes.POINTER(ctypes.c_uint),
    event: ctypes.POINTER(vxlapi.XLevent),
) -> int:
    event.tag = vxlapi.XL_RECEIVE_MSG
    event.tagData.msg.id = 0x123
    event.tagData.msg.dlc = 8
    event.tagData.msg.flags = 0
    event.timeStamp = 0
    event.chanIndex = 0
    for idx, value in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        event.tagData.msg.data[idx] = value
    return 0


def xlCanReceive(
    port_handle: vxlapi.XLportHandle, event: ctypes.POINTER(vxlapi.XLcanRxEvent)
) -> int:
    event.tag = vxlapi.XL_CAN_EV_TAG_RX_OK
    event.tagData.canRxOkMsg.canId = 0x123
    event.tagData.canRxOkMsg.dlc = 8
    event.tagData.canRxOkMsg.msgFlags = 0
    event.timeStamp = 0
    event.chanIndex = 0
    for idx, value in enumerate([1, 2, 3, 4, 5, 6, 7, 8]):
        event.tagData.canRxOkMsg.data[idx] = value
    return 0


def xlCanTransmit(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    message_count: ctypes.POINTER(ctypes.c_uint),
    xl_event: ctypes.POINTER(vxlapi.XLevent),
) -> int:
    return 0


def xlCanTransmitEx(
    port_handle: vxlapi.XLportHandle,
    access_mask: vxlapi.XLaccess,
    message_count: ctypes.c_uint,
    MsgCntSent: ctypes.POINTER(ctypes.c_uint),
    XLcanTxEvent: ctypes.POINTER(vxlapi.XLcanTxEvent),
) -> int:
    return 0


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python

"""
Test for Vector Interface
"""
import contextlib
import ctypes
import os
import pickle
import random
import unittest
from typing import List
from unittest.mock import Mock

import pytest

import can
from can.interfaces.vector import (
    canlib,
    xldefine,
    xlclass,
    VectorError,
    VectorInitializationError,
    VectorOperationError,
    VectorChannelConfig,
)
from can.interfaces.vector.canlib import VectorBusParams
from test.config import IS_WINDOWS

MOCK = True
try:
    from can.interfaces.vector import xldriver

    # test real driver if available
    MOCK = False
except Exception:
    pass


class TestVectorBus(unittest.TestCase):
    def setUp(self) -> None:

        if MOCK:
            # mock channel configuration
            canlib.get_channel_configs = Mock(
                side_effect=get_channel_configs,
            )

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
            can.interfaces.vector.canlib.xldriver.xlOpenPort = Mock(
                side_effect=xlOpenPort
            )
            can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration = Mock(
                return_value=0
            )
            can.interfaces.vector.canlib.xldriver.xlCanSetChannelMode = Mock(
                return_value=0
            )
            can.interfaces.vector.canlib.xldriver.xlActivateChannel = Mock(
                return_value=0
            )
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
            can.interfaces.vector.canlib.xldriver.xlDeactivateChannel = Mock(
                return_value=0
            )
            can.interfaces.vector.canlib.xldriver.xlClosePort = Mock(return_value=0)
            can.interfaces.vector.canlib.xldriver.xlCloseDriver = Mock()

            # sender functions
            can.interfaces.vector.canlib.xldriver.xlCanTransmit = Mock(return_value=0)
            can.interfaces.vector.canlib.xldriver.xlCanTransmitEx = Mock(return_value=0)

            # various functions
            can.interfaces.vector.canlib.xldriver.xlCanFlushTransmitQueue = Mock()
            can.interfaces.vector.canlib.xldriver.xlSetTimerRate = Mock()
            can.interfaces.vector.canlib.xldriver.xlGenerateSyncPulse = Mock()
            can.interfaces.vector.canlib.xldriver.xlFlushReceiveQueue = Mock()
            can.interfaces.vector.canlib.WaitForSingleObject = Mock()

        self.bus = None

    def tearDown(self) -> None:
        if self.bus:
            with contextlib.suppress(canlib.VectorOperationError):
                self.bus.shutdown()
            self.bus = None

    def test_bus_creation(self) -> None:
        if MOCK:
            self.bus = can.Bus(
                app_name="test_bus_creation",
                bustype="vector",
                channel=0,
                _testing=True,
            )
            self.assertIsInstance(self.bus, canlib.VectorBus)

            can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
            can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

            can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
            xlOpenPort_args = (
                can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
            )
            self.assertEqual(
                xlOpenPort_args[5],
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value,
            )
            self.assertEqual(
                xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value
            )

            can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
            can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()
        else:
            self.bus = can.Bus(
                app_name="test_bus_creation",
                bustype="vector",
                channel=0,
                serial=100,
                _testing=True,
            )
            self.assertIsInstance(self.bus, canlib.VectorBus)

            vcc = _find_channel_configuration(100, 0)
            assert vcc.busParams.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
            assert (
                vcc.busParams.can_params["can_op_mode"]
                is xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CAN20
            )
            assert vcc.isOnBus

    def test_bus_creation_bitrate(self) -> None:
        self.bus = can.Bus(
            app_name="test_bus_creation_bitrate",
            bustype="vector",
            channel=0,
            serial=100,
            bitrate=200_000,
            _testing=True,
        )
        self.assertIsInstance(self.bus, canlib.VectorBus)

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
            can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
            xlOpenPort_args = (
                can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
            )
            self.assertEqual(
                xlOpenPort_args[5],
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value,
            )
            self.assertEqual(
                xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value
            )

            can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
            can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_called()
            xlCanSetChannelBitrate_args = (
                can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.call_args[
                    0
                ]
            )
            self.assertEqual(xlCanSetChannelBitrate_args[2], 200_000)
        else:
            vcc = _find_channel_configuration(100, 0)
            assert vcc.busParams.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
            assert (
                vcc.busParams.can_params["can_op_mode"]
                in xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CAN20
            )
            assert vcc.busParams.can_params["bitrate"] == 200_000
            assert vcc.isOnBus

    def test_bus_creation_fd(self) -> None:
        self.bus = can.Bus(
            app_name="test_bus_creation_fd",
            channel=0,
            serial=100,
            bitrate=500_000,
            data_bitrate=1_000_000,
            fd=True,
            bustype="vector",
            _testing=True,
        )
        self.assertIsInstance(self.bus, canlib.VectorBus)

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
            can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
            xlOpenPort_args = (
                can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
            )
            self.assertEqual(
                xlOpenPort_args[5],
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
            )
            self.assertEqual(
                xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value
            )

            can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()
        else:
            vcc = _find_channel_configuration(100, 0)
            assert vcc.busParams.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
            assert (
                xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CANFD
                in vcc.busParams.canfd_params["can_op_mode"]
            )
            assert vcc.busParams.canfd_params["bitrate"] == 500_000
            assert vcc.busParams.canfd_params["data_bitrate"] == 1_000_000
            assert vcc.isOnBus

    def test_bus_creation_fd_bitrate_timings(self) -> None:
        self.bus = can.Bus(
            app_name="test_bus_creation_fd_bitrate_timings",
            serial=100,
            channel=0,
            bustype="vector",
            fd=True,
            bitrate=500_000,
            data_bitrate=5_000_000,
            sjw_abr=32,
            tseg1_abr=127,
            tseg2_abr=32,
            sjw_dbr=6,
            tseg1_dbr=9,
            tseg2_dbr=6,
            _testing=True,
        )
        self.assertIsInstance(self.bus, canlib.VectorBus)

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
            can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
            xlOpenPort_args = (
                can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
            )
            self.assertEqual(
                xlOpenPort_args[5],
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
            )
            self.assertEqual(
                xlOpenPort_args[6], xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value
            )

            can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()

            xlCanFdSetConfiguration_args = (
                can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.call_args[
                    0
                ]
            )
            canFdConf = xlCanFdSetConfiguration_args[2]
            self.assertEqual(canFdConf.arbitrationBitRate, 500_000)
            self.assertEqual(canFdConf.dataBitRate, 5_000_000)
            self.assertEqual(canFdConf.sjwAbr, 32)
            self.assertEqual(canFdConf.tseg1Abr, 127)
            self.assertEqual(canFdConf.tseg2Abr, 32)
            self.assertEqual(canFdConf.sjwDbr, 6)
            self.assertEqual(canFdConf.tseg1Dbr, 9)
            self.assertEqual(canFdConf.tseg2Dbr, 6)
        else:
            vcc = _find_channel_configuration(100, 0)
            assert vcc.busParams.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
            assert (
                xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CANFD
                in vcc.busParams.canfd_params["can_op_mode"]
            )
            assert vcc.busParams.canfd_params["bitrate"] == 500_000
            assert vcc.busParams.canfd_params["data_bitrate"] == 5_000_000
            assert vcc.busParams.canfd_params["sjw_abr"] == 32
            assert vcc.busParams.canfd_params["tseg1_abr"] == 127
            assert vcc.busParams.canfd_params["tseg2_abr"] == 32
            assert vcc.busParams.canfd_params["sjw_dbr"] == 6
            assert vcc.busParams.canfd_params["tseg1_dbr"] == 9
            assert vcc.busParams.canfd_params["tseg2_dbr"] == 6

            assert vcc.isOnBus

    def test_receive(self) -> None:
        self.bus = can.Bus(
            app_name="test_receive",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
            receive_own_messages=True,
        )
        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlReceive = Mock(
                side_effect=xlReceive
            )
            self.bus.recv(timeout=0.05)
            can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()
        else:
            tx_msg = can.Message(
                channel=0,
                arbitration_id=100,
                is_extended_id=False,
                data=random.randbytes(8),
                is_rx=False,
                dlc=8,
            )
            self.bus.send(tx_msg)
            rx_msg = self.bus.recv()
            assert tx_msg.equals(rx_msg, timestamp_delta=None)

    def test_receive_fd(self) -> None:
        self.bus = canlib.VectorBus(
            app_name="test_receive_fd",
            channel=0,
            serial=100,
            fd=True,
            bitrate=500_000,
            data_bitrate=5_000_000,
            sjw_abr=32,
            tseg1_abr=127,
            tseg2_abr=32,
            sjw_dbr=6,
            tseg1_dbr=9,
            tseg2_dbr=6,
            receive_own_messages=True,
            _testing=True,
        )

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(
                side_effect=xlCanReceive
            )
            self.bus.recv(timeout=0.05)
            can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
            can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()
        else:
            tx_msg = can.Message(
                channel=0,
                arbitration_id=100,
                is_extended_id=False,
                is_fd=True,
                data=random.randbytes(32),
                is_rx=False,
                bitrate_switch=True,
            )
            self.bus.send(tx_msg)
            rx_msg = self.bus.recv(1.0)
            assert tx_msg.equals(rx_msg, timestamp_delta=None)

    def test_receive_non_msg_event(self) -> None:
        self.bus = canlib.VectorBus(
            app_name="test_receive_non_msg_event",
            serial=100,
            channel=0,
            _testing=True,
        )
        self.bus.handle_can_event = Mock()

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlReceive = Mock(
                side_effect=xlReceive_chipstate
            )

            self.bus.recv(timeout=0.05)
            can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()
            self.bus.handle_can_event.assert_called()
        else:
            # request and receive chipstate
            self.bus.request_chip_state()
            while self.bus.recv(-1.0):
                pass
            self.bus.handle_can_event.assert_called()

    def test_receive_fd_non_msg_event(self) -> None:
        self.bus = canlib.VectorBus(
            app_name="test_receive_fd_non_msg_event",
            serial=100,
            channel=0,
            fd=True,
            _testing=True,
        )
        self.bus.handle_canfd_event = Mock()

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(
                side_effect=xlCanReceive_chipstate
            )
            self.bus.handle_canfd_event = Mock()
            self.bus.recv(timeout=0.05)
            self.bus.handle_canfd_event.assert_called()
            can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
            can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()
        else:
            self.bus.request_chip_state()
            while self.bus.recv(-1):
                pass
            self.bus.handle_canfd_event.assert_called()

    def test_send(self) -> None:
        self.bus = can.Bus(
            app_name="test_send", serial=100, channel=0, bustype="vector", _testing=True
        )
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_not_called()

    def test_send_fd(self) -> None:
        self.bus = can.Bus(
            app_name="test_send_fd",
            serial=100,
            channel=0,
            fd=True,
            bitrate=500_000,
            data_bitrate=5_000_000,
            sjw_abr=32,
            tseg1_abr=127,
            tseg2_abr=32,
            sjw_dbr=6,
            tseg1_dbr=9,
            tseg2_dbr=6,
            bustype="vector",
            _testing=True,
        )
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_not_called()
            can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_called()

    def test_flush_tx_buffer(self) -> None:
        self.bus = can.Bus(
            app_name="test_flush_tx_buffer",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.flush_tx_buffer()

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlCanFlushTransmitQueue.assert_called()

    def test_shutdown(self) -> None:
        self.bus = can.Bus(
            app_name="test_shutdown",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.shutdown()

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
            can.interfaces.vector.canlib.xldriver.xlClosePort.assert_called()
            can.interfaces.vector.canlib.xldriver.xlCloseDriver.assert_called()

    def test_reset(self) -> None:
        self.bus = can.Bus(
            app_name="test_reset",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.reset()

        if MOCK:
            can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
            can.interfaces.vector.canlib.xldriver.xlActivateChannel.assert_called()

    def test_popup_hw_cfg(self) -> None:
        if MOCK:
            canlib.xldriver.xlPopupHwConfig = Mock()
            canlib.VectorBus.popup_vector_hw_configuration(10)
            assert canlib.xldriver.xlPopupHwConfig.called
            args, kwargs = canlib.xldriver.xlPopupHwConfig.call_args
            assert isinstance(args[0], ctypes.c_char_p)
            assert isinstance(args[1], ctypes.c_uint)
        else:
            canlib.VectorBus.popup_vector_hw_configuration(0)

    def test_get_application_config(self) -> None:
        if MOCK:
            canlib.xldriver.xlGetApplConfig = Mock()
            canlib.VectorBus.get_application_config(app_name="CANalyzer", app_channel=0)
            assert canlib.xldriver.xlGetApplConfig.called
        else:
            hw_type, hw_index, hw_channel = canlib.VectorBus.get_application_config(
                app_name="CANalyzer", app_channel=0
            )
            assert isinstance(hw_type, xldefine.XL_HardwareType)
            assert isinstance(hw_index, int)
            assert isinstance(hw_index, int)

    def test_set_application_config(self) -> None:
        canlib.xldriver.xlSetApplConfig = Mock()
        canlib.VectorBus.set_application_config(
            app_name="CANalyzer",
            app_channel=0,
            hw_type=xldefine.XL_HardwareType.XL_HWTYPE_VN1610,
            hw_index=0,
            hw_channel=0,
        )
        assert canlib.xldriver.xlSetApplConfig.called

    def test_set_timer_rate(self) -> None:
        bus: canlib.VectorBus = can.Bus(
            app_name="test_set_timer_rate",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        bus.set_timer_rate(timer_rate_ms=1)

        if MOCK:
            assert canlib.xldriver.xlSetTimerRate.called

    def test_flush_rx_buffer(self) -> None:
        self.bus: canlib.VectorBus = can.Bus(
            app_name="test_flush_rx_buffer",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.flush_rx_buffer()

        if MOCK:
            assert canlib.xldriver.xlFlushReceiveQueue.called

    def test_request_chip_state(self) -> None:
        self.bus: canlib.VectorBus = can.Bus(
            app_name="test_request_chip_state",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.request_chip_state()

        if MOCK:
            assert canlib.xldriver.xlCanRequestChipState.called

    def test_generate_sync_pulse(self) -> None:
        self.bus: canlib.VectorBus = can.Bus(
            app_name="test_generate_sync_pulse",
            serial=100,
            channel=0,
            bustype="vector",
            _testing=True,
        )
        self.bus.generate_sync_pulse(channel=0)

        if MOCK:
            assert canlib.xldriver.xlGenerateSyncPulse.called

    def test_called_without_testing_argument(self) -> None:
        """This tests if an exception is thrown when we are not running on Windows."""
        if os.name != "nt":
            with self.assertRaises(can.CanInterfaceNotImplementedError):
                # do not set the _testing argument, since it would suppress the exception
                can.Bus(
                    app_name="test_called_without_testing_argument",
                    channel=0,
                    bustype="vector",
                )

    def test_vector_error_pickle(self) -> None:
        for error_type in [
            VectorError,
            VectorInitializationError,
            VectorOperationError,
        ]:
            with self.subTest(f"error_type = {error_type.__name__}"):

                error_code = 118
                error_string = "XL_ERROR"
                function = "function_name"

                exc = error_type(error_code, error_string, function)

                # pickle and unpickle
                p = pickle.dumps(exc)
                exc_unpickled: VectorError = pickle.loads(p)

                self.assertEqual(str(exc), str(exc_unpickled))
                self.assertEqual(error_code, exc_unpickled.error_code)

                with pytest.raises(error_type):
                    raise exc_unpickled

    def test_vector_subtype_error_from_generic(self) -> None:
        for error_type in [VectorInitializationError, VectorOperationError]:
            with self.subTest(f"error_type = {error_type.__name__}"):

                error_code = 118
                error_string = "XL_ERROR"
                function = "function_name"

                generic = VectorError(error_code, error_string, function)

                # pickle and unpickle
                specific: VectorError = error_type.from_generic(generic)

                self.assertEqual(str(generic), str(specific))
                self.assertEqual(error_code, specific.error_code)

                with pytest.raises(error_type):
                    raise specific

    @unittest.skipUnless(IS_WINDOWS, "Windows specific test")
    def test_winapi_availability(self) -> None:
        self.assertIsNotNone(canlib.WaitForSingleObject)
        self.assertIsNotNone(canlib.INFINITE)


class TestVectorChannelConfig:
    def test_attributes(self):
        assert hasattr(VectorChannelConfig, "name")
        assert hasattr(VectorChannelConfig, "hwType")
        assert hasattr(VectorChannelConfig, "hwIndex")
        assert hasattr(VectorChannelConfig, "hwChannel")
        assert hasattr(VectorChannelConfig, "channelIndex")
        assert hasattr(VectorChannelConfig, "channelMask")
        assert hasattr(VectorChannelConfig, "channelCapabilities")
        assert hasattr(VectorChannelConfig, "channelBusCapabilities")
        assert hasattr(VectorChannelConfig, "isOnBus")
        assert hasattr(VectorChannelConfig, "connectedBusType")
        assert hasattr(VectorChannelConfig, "busParams")
        assert hasattr(VectorChannelConfig, "driverVersion")
        assert hasattr(VectorChannelConfig, "interfaceVersion")
        assert hasattr(VectorChannelConfig, "serialNumber")
        assert hasattr(VectorChannelConfig, "articleNumber")
        assert hasattr(VectorChannelConfig, "transceiverName")


class TestVectorBusParams:
    def test_attributes(self):
        assert hasattr(VectorBusParams, "bus_type")
        assert hasattr(VectorBusParams, "can_params")
        assert hasattr(VectorBusParams, "canfd_params")

    def test_from_bus_params(self):
        # test CAN
        can_bus_params_bytes = bytes.fromhex(
            "01 00 00 00 20 a1 07 00 01 04 03 01 01 00 00 00 "
            "00 00 00 00 01 00 00 00 00 68 89 09 00 00 00 00"
        )
        can_bus_params = xlclass.XLbusParams.from_buffer_copy(can_bus_params_bytes)
        bus_params = VectorBusParams.from_bus_params(can_bus_params)
        assert bus_params.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
        assert bus_params.can_params["bitrate"] == 500_000
        assert bus_params.can_params["sjw"] == 1
        assert bus_params.can_params["tseg1"] == 4
        assert bus_params.can_params["tseg2"] == 3
        assert bus_params.can_params["sam"] == 1
        assert (
            bus_params.can_params["output_mode"]
            is xldefine.XL_OutputMode.XL_OUTPUT_MODE_NORMAL
        )
        assert (
            bus_params.can_params["can_op_mode"]
            is xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CAN20
        )

        # test CAN FD
        canfd_bus_params_bytes = bytes.fromhex(
            "01 00 00 00 20 a1 07 00 02 06 03 01 01 02 06 03 "
            "80 84 1e 00 06 00 00 00 00 68 89 09 00 00 00 00"
        )
        canfd_bus_params = xlclass.XLbusParams.from_buffer_copy(canfd_bus_params_bytes)
        bus_params = VectorBusParams.from_bus_params(canfd_bus_params)
        assert bus_params.bus_type is xldefine.XL_BusTypes.XL_BUS_TYPE_CAN
        assert bus_params.canfd_params["bitrate"] == 500_000
        assert bus_params.canfd_params["data_bitrate"] == 2_000_000
        assert bus_params.canfd_params["sjw_abr"] == 2
        assert bus_params.canfd_params["tseg1_abr"] == 6
        assert bus_params.canfd_params["tseg2_abr"] == 3
        assert bus_params.canfd_params["sam_abr"] == 1
        assert bus_params.canfd_params["sjw_dbr"] == 2
        assert bus_params.canfd_params["tseg1_dbr"] == 6
        assert bus_params.canfd_params["tseg2_dbr"] == 3
        assert (
            bus_params.canfd_params["output_mode"]
            is xldefine.XL_OutputMode.XL_OUTPUT_MODE_NORMAL
        )
        assert (
            xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CANFD
            in bus_params.canfd_params["can_op_mode"]
        )


def xlGetApplConfig(
    app_name_p: bytes,
    app_channel: ctypes.c_uint,
    hw_type: ctypes.c_uint,
    hw_index: ctypes.c_uint,
    hw_channel: ctypes.c_uint,
    bus_type: xldefine.XL_BusTypes,
) -> int:
    hw_type.value = 1
    hw_channel.value = 0
    return 0


def xlGetChannelIndex(
    hw_type: xldefine.XL_HardwareType, hw_index: int, hw_channel: int
) -> int:
    return hw_channel


def xlOpenPort(
    port_handle_p: xlclass.XLportHandle,
    app_name_p: bytes,
    access_mask: int,
    permission_mask_p: xlclass.XLaccess,
    rx_queue_size: int,
    xl_interface_version: xldefine.XL_InterfaceVersion,
    bus_type: xldefine.XL_BusTypes,
) -> int:
    port_handle_p.value = 0
    permission_mask_p.value = access_mask
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
    event_count_p: ctypes.c_uint,
    event: xlclass.XLevent,
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


def xlCanReceive(port_handle: xlclass.XLportHandle, event: xlclass.XLcanRxEvent) -> int:
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
    event_count_p: ctypes.c_uint,
    event: xlclass.XLevent,
) -> int:
    event.tag = xldefine.XL_EventTags.XL_CHIP_STATE.value
    event.tagData.chipState.busStatus = 8
    event.tagData.chipState.rxErrorCounter = 0
    event.tagData.chipState.txErrorCounter = 0
    event.timeStamp = 0
    event.chanIndex = 2
    return 0


def xlCanReceive_chipstate(
    port_handle: xlclass.XLportHandle, event: xlclass.XLcanRxEvent
) -> int:
    event.tag = xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_CHIP_STATE.value
    event.tagData.canChipState.busStatus = 8
    event.tagData.canChipState.rxErrorCounter = 0
    event.tagData.canChipState.txErrorCounter = 0
    event.timeStamp = 0
    event.chanIndex = 2
    return 0


def get_channel_configs() -> List[VectorChannelConfig]:
    raw_data = """
    56 69 72 74 75 61 6c 20 43 68 61 6e 6e 65 6c 20 31 00 00 00 00 00 
    00 00 00 00 00 00 00 00 00 00 01 00 00 16 00 00 00 00 00 00 01 00 
    00 00 00 00 00 00 07 00 00 a0 01 00 01 00 00 00 00 00 00 01 00 00 
    00 20 a1 07 00 01 04 03 01 01 00 00 00 00 00 00 00 01 00 00 00 00 
    68 89 09 00 00 00 00 00 00 00 00 14 00 0a 15 04 00 00 00 00 00 00 
    00 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00 00 00 00 00 00 00 
    00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 64 00 00 00 58 1b 00 
    00 56 69 72 74 75 61 6c 20 43 41 4e 00 00 00 00 00 00 00 00 00 00 
    00 00 00 00 00 00 00 00 00 00 00 04 00 00 00 00 00 00 00 00 00 00 
    02 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
    00 00 00 00 00 00 00
    """
    xlcc = xlclass.XLchannelConfig.from_buffer_copy(bytes.fromhex(raw_data))
    return [
        VectorChannelConfig(
            name=xlcc.name.decode(),
            hwType=xldefine.XL_HardwareType(xlcc.hwType),
            hwIndex=xlcc.hwIndex,
            hwChannel=xlcc.hwChannel,
            channelIndex=xlcc.channelIndex,
            channelMask=xlcc.channelMask,
            channelCapabilities=xldefine.XL_ChannelCapabilities(
                xlcc.channelCapabilities
            ),
            channelBusCapabilities=xldefine.XL_BusCapabilities(
                xlcc.channelBusCapabilities
            ),
            isOnBus=bool(xlcc.isOnBus),
            connectedBusType=xldefine.XL_BusTypes(xlcc.connectedBusType),
            busParams=canlib.VectorBusParams.from_bus_params(xlcc.busParams),
            driverVersion=".".join(
                [str(x) for x in xlcc.driverVersion.to_bytes(4, "little")]
            ),
            interfaceVersion=xldefine.XL_InterfaceVersion(xlcc.interfaceVersion),
            serialNumber=xlcc.serialNumber,
            articleNumber=xlcc.articleNumber,
            transceiverName=xlcc.transceiverName.decode(),
        )
    ]


def _find_channel_configuration(
    serial: int,
    channel: int,
) -> VectorChannelConfig:
    vcc_list = canlib.get_channel_configs()
    for vcc in vcc_list:
        if serial != vcc.serialNumber:
            continue
        if channel != vcc.hwChannel:
            continue
        return vcc


if __name__ == "__main__":
    unittest.main()

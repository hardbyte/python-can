#!/usr/bin/env python

"""
Test for Vector Interface
"""

import ctypes
import functools
import pickle
import sys
import time
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
from can.interfaces.vector import VectorBusParams, VectorCanParams, VectorCanFdParams
from test.config import IS_WINDOWS

XLDRIVER_FOUND = canlib.xldriver is not None


@pytest.fixture()
def mock_xldriver() -> None:
    # basic mock for XLDriver
    xldriver_mock = Mock()

    # bus creation functions
    xldriver_mock.xlOpenDriver = Mock()
    xldriver_mock.xlGetApplConfig = Mock(side_effect=xlGetApplConfig)
    xldriver_mock.xlGetChannelIndex = Mock(side_effect=xlGetChannelIndex)
    xldriver_mock.xlOpenPort = Mock(side_effect=xlOpenPort)
    xldriver_mock.xlCanFdSetConfiguration = Mock(return_value=0)
    xldriver_mock.xlCanSetChannelMode = Mock(return_value=0)
    xldriver_mock.xlActivateChannel = Mock(return_value=0)
    xldriver_mock.xlGetSyncTime = Mock(side_effect=xlGetSyncTime)
    xldriver_mock.xlCanSetChannelAcceptance = Mock(return_value=0)
    xldriver_mock.xlCanSetChannelBitrate = Mock(return_value=0)
    xldriver_mock.xlSetNotification = Mock(side_effect=xlSetNotification)

    # bus deactivation functions
    xldriver_mock.xlDeactivateChannel = Mock(return_value=0)
    xldriver_mock.xlClosePort = Mock(return_value=0)
    xldriver_mock.xlCloseDriver = Mock()

    # sender functions
    xldriver_mock.xlCanTransmit = Mock(return_value=0)
    xldriver_mock.xlCanTransmitEx = Mock(return_value=0)

    # various functions
    xldriver_mock.xlCanFlushTransmitQueue = Mock()

    # backup unmodified values
    real_xldriver = canlib.xldriver
    real_waitforsingleobject = canlib.WaitForSingleObject
    real_has_events = canlib.HAS_EVENTS

    # set mock
    canlib.xldriver = xldriver_mock
    canlib.HAS_EVENTS = False

    yield

    # cleanup
    canlib.xldriver = real_xldriver
    canlib.WaitForSingleObject = real_waitforsingleobject
    canlib.HAS_EVENTS = real_has_events


def test_bus_creation_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    assert isinstance(bus, canlib.VectorBus)
    can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
    can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

    can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
    xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
    assert xlOpenPort_args[5] == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value
    assert xlOpenPort_args[6] == xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value

    can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
    can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_bus_creation() -> None:
    bus = can.Bus(channel=0, serial=_find_virtual_can_serial(), bustype="vector")
    assert isinstance(bus, canlib.VectorBus)
    bus.shutdown()

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert bus.channel_masks[0] == xl_channel_config.channelMask
    assert (
        xl_channel_config.busParams.data.can.canOpMode
        & xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CAN20
    )

    bus = canlib.VectorBus(channel=0, serial=_find_virtual_can_serial())
    assert isinstance(bus, canlib.VectorBus)
    bus.shutdown()


def test_bus_creation_bitrate_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", bitrate=200_000, _testing=True)
    assert isinstance(bus, canlib.VectorBus)
    can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
    can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

    can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
    xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
    assert xlOpenPort_args[5] == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value
    assert xlOpenPort_args[6] == xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value

    can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_not_called()
    can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_called()
    xlCanSetChannelBitrate_args = (
        can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.call_args[0]
    )
    assert xlCanSetChannelBitrate_args[2] == 200_000


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_bus_creation_bitrate() -> None:
    bus = can.Bus(
        channel=0, serial=_find_virtual_can_serial(), bustype="vector", bitrate=200_000
    )
    assert isinstance(bus, canlib.VectorBus)

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert xl_channel_config.busParams.data.can.bitRate == 200_000

    bus.shutdown()


def test_bus_creation_fd_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
    assert isinstance(bus, canlib.VectorBus)
    can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
    can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

    can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
    xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
    assert (
        xlOpenPort_args[5] == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value
    )
    assert xlOpenPort_args[6] == xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value

    can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_bus_creation_fd() -> None:
    bus = can.Bus(
        channel=0, serial=_find_virtual_can_serial(), bustype="vector", fd=True
    )
    assert isinstance(bus, canlib.VectorBus)

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert (
        xl_channel_config.interfaceVersion
        == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4
    )
    assert (
        xl_channel_config.busParams.data.canFD.canOpMode
        & xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CANFD
    )
    bus.shutdown()


def test_bus_creation_fd_bitrate_timings_mocked(mock_xldriver) -> None:
    bus = can.Bus(
        channel=0,
        bustype="vector",
        fd=True,
        bitrate=500_000,
        data_bitrate=2_000_000,
        sjw_abr=10,
        tseg1_abr=11,
        tseg2_abr=12,
        sjw_dbr=13,
        tseg1_dbr=14,
        tseg2_dbr=15,
        _testing=True,
    )
    assert isinstance(bus, canlib.VectorBus)
    can.interfaces.vector.canlib.xldriver.xlOpenDriver.assert_called()
    can.interfaces.vector.canlib.xldriver.xlGetApplConfig.assert_called()

    can.interfaces.vector.canlib.xldriver.xlOpenPort.assert_called()
    xlOpenPort_args = can.interfaces.vector.canlib.xldriver.xlOpenPort.call_args[0]
    assert (
        xlOpenPort_args[5] == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value
    )

    assert xlOpenPort_args[6] == xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value

    can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCanSetChannelBitrate.assert_not_called()

    xlCanFdSetConfiguration_args = (
        can.interfaces.vector.canlib.xldriver.xlCanFdSetConfiguration.call_args[0]
    )
    canFdConf = xlCanFdSetConfiguration_args[2]
    assert canFdConf.arbitrationBitRate == 500000
    assert canFdConf.dataBitRate == 2000000
    assert canFdConf.sjwAbr == 10
    assert canFdConf.tseg1Abr == 11
    assert canFdConf.tseg2Abr == 12
    assert canFdConf.sjwDbr == 13
    assert canFdConf.tseg1Dbr == 14
    assert canFdConf.tseg2Dbr == 15


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_bus_creation_fd_bitrate_timings() -> None:
    bus = can.Bus(
        channel=0,
        serial=_find_virtual_can_serial(),
        bustype="vector",
        fd=True,
        bitrate=500_000,
        data_bitrate=2_000_000,
        sjw_abr=10,
        tseg1_abr=11,
        tseg2_abr=12,
        sjw_dbr=13,
        tseg1_dbr=14,
        tseg2_dbr=15,
    )

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert (
        xl_channel_config.interfaceVersion
        == xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4
    )
    assert (
        xl_channel_config.busParams.data.canFD.canOpMode
        & xldefine.XL_CANFD_BusParams_CanOpMode.XL_BUS_PARAMS_CANOPMODE_CANFD
    )
    assert xl_channel_config.busParams.data.canFD.arbitrationBitRate == 500_000
    assert xl_channel_config.busParams.data.canFD.sjwAbr == 10
    assert xl_channel_config.busParams.data.canFD.tseg1Abr == 11
    assert xl_channel_config.busParams.data.canFD.tseg2Abr == 12
    assert xl_channel_config.busParams.data.canFD.sjwDbr == 13
    assert xl_channel_config.busParams.data.canFD.tseg1Dbr == 14
    assert xl_channel_config.busParams.data.canFD.tseg2Dbr == 15
    assert xl_channel_config.busParams.data.canFD.dataBitRate == 2_000_000

    bus.shutdown()


def test_send_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    msg = can.Message(
        arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
    )
    bus.send(msg)
    can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_not_called()


def test_send_fd_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
    msg = can.Message(
        arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
    )
    bus.send(msg)
    can.interfaces.vector.canlib.xldriver.xlCanTransmit.assert_not_called()
    can.interfaces.vector.canlib.xldriver.xlCanTransmitEx.assert_called()


def test_receive_mocked(mock_xldriver) -> None:
    can.interfaces.vector.canlib.xldriver.xlReceive = Mock(side_effect=xlReceive)
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    bus.recv(timeout=0.05)
    can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()


def test_receive_fd_mocked(mock_xldriver) -> None:
    can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(side_effect=xlCanReceive)
    bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
    bus.recv(timeout=0.05)
    can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
    can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_send_and_receive() -> None:
    bus1 = can.Bus(channel=0, serial=_find_virtual_can_serial(), bustype="vector")
    bus2 = can.Bus(channel=0, serial=_find_virtual_can_serial(), bustype="vector")

    msg_std = can.Message(
        channel=0, arbitration_id=0xFF, data=list(range(8)), is_extended_id=False
    )
    msg_ext = can.Message(
        channel=0, arbitration_id=0xFFFFFF, data=list(range(8)), is_extended_id=True
    )

    bus1.send(msg_std)
    msg_std_recv = bus2.recv(None)
    assert msg_std.equals(msg_std_recv, timestamp_delta=None)

    bus1.send(msg_ext)
    msg_ext_recv = bus2.recv(None)
    assert msg_ext.equals(msg_ext_recv, timestamp_delta=None)

    bus1.shutdown()
    bus2.shutdown()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_send_and_receive_fd() -> None:
    bus1 = can.Bus(
        channel=0, serial=_find_virtual_can_serial(), fd=True, bustype="vector"
    )
    bus2 = can.Bus(
        channel=0, serial=_find_virtual_can_serial(), fd=True, bustype="vector"
    )

    msg_std = can.Message(
        channel=0,
        arbitration_id=0xFF,
        data=list(range(64)),
        is_extended_id=False,
        is_fd=True,
    )
    msg_ext = can.Message(
        channel=0,
        arbitration_id=0xFFFFFF,
        data=list(range(64)),
        is_extended_id=True,
        is_fd=True,
    )

    bus1.send(msg_std)
    msg_std_recv = bus2.recv(None)
    assert msg_std.equals(msg_std_recv, timestamp_delta=None)

    bus1.send(msg_ext)
    msg_ext_recv = bus2.recv(None)
    assert msg_ext.equals(msg_ext_recv, timestamp_delta=None)

    bus1.shutdown()
    bus2.shutdown()


def test_receive_non_msg_event_mocked(mock_xldriver) -> None:
    can.interfaces.vector.canlib.xldriver.xlReceive = Mock(
        side_effect=xlReceive_chipstate
    )
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    bus.handle_can_event = Mock()
    bus.recv(timeout=0.05)
    can.interfaces.vector.canlib.xldriver.xlReceive.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_not_called()
    bus.handle_can_event.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_receive_non_msg_event() -> None:
    bus = canlib.VectorBus(
        channel=0, serial=_find_virtual_can_serial(), bustype="vector"
    )
    bus.handle_can_event = Mock()
    bus.xldriver.xlCanRequestChipState(bus.port_handle, bus.channel_masks[0])
    bus.recv(timeout=0.5)
    bus.handle_can_event.assert_called()
    bus.shutdown()


def test_receive_fd_non_msg_event_mocked(mock_xldriver) -> None:
    can.interfaces.vector.canlib.xldriver.xlCanReceive = Mock(
        side_effect=xlCanReceive_chipstate
    )
    bus = can.Bus(channel=0, bustype="vector", fd=True, _testing=True)
    bus.handle_canfd_event = Mock()
    bus.recv(timeout=0.05)
    can.interfaces.vector.canlib.xldriver.xlReceive.assert_not_called()
    can.interfaces.vector.canlib.xldriver.xlCanReceive.assert_called()
    bus.handle_canfd_event.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_receive_fd_non_msg_event() -> None:
    bus = canlib.VectorBus(
        channel=0, serial=_find_virtual_can_serial(), fd=True, bustype="vector"
    )
    bus.handle_canfd_event = Mock()
    bus.xldriver.xlCanRequestChipState(bus.port_handle, bus.channel_masks[0])
    bus.recv(timeout=0.5)
    bus.handle_canfd_event.assert_called()
    bus.shutdown()


def test_flush_tx_buffer_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    bus.flush_tx_buffer()
    can.interfaces.vector.canlib.xldriver.xlCanFlushTransmitQueue.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_flush_tx_buffer() -> None:
    bus = can.Bus(channel=0, serial=_find_virtual_can_serial(), bustype="vector")
    bus.flush_tx_buffer()
    bus.shutdown()


def test_shutdown_mocked(mock_xldriver) -> None:
    bus = can.Bus(channel=0, bustype="vector", _testing=True)
    bus.shutdown()
    can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
    can.interfaces.vector.canlib.xldriver.xlClosePort.assert_called()
    can.interfaces.vector.canlib.xldriver.xlCloseDriver.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_shutdown() -> None:
    bus = can.Bus(channel=0, serial=_find_virtual_can_serial(), bustype="vector")

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert xl_channel_config.isOnBus != 0
    bus.shutdown()

    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=0
    )
    assert xl_channel_config.isOnBus == 0


def test_reset_mocked(mock_xldriver) -> None:
    bus = canlib.VectorBus(channel=0, bustype="vector", _testing=True)
    bus.reset()
    can.interfaces.vector.canlib.xldriver.xlDeactivateChannel.assert_called()
    can.interfaces.vector.canlib.xldriver.xlActivateChannel.assert_called()


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_reset_mocked() -> None:
    bus = canlib.VectorBus(
        channel=0, serial=_find_virtual_can_serial(), bustype="vector"
    )
    bus.reset()
    bus.shutdown()


def test_popup_hw_cfg_mocked(mock_xldriver) -> None:
    canlib.xldriver.xlPopupHwConfig = Mock()
    canlib.VectorBus.popup_vector_hw_configuration(10)
    assert canlib.xldriver.xlPopupHwConfig.called
    args, kwargs = canlib.xldriver.xlPopupHwConfig.call_args
    assert isinstance(args[0], ctypes.c_char_p)
    assert isinstance(args[1], ctypes.c_uint)


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_popup_hw_cfg() -> None:
    with pytest.raises(VectorOperationError):
        canlib.VectorBus.popup_vector_hw_configuration(1)


def test_get_application_config_mocked(mock_xldriver) -> None:
    canlib.xldriver.xlGetApplConfig = Mock()
    canlib.VectorBus.get_application_config(app_name="CANalyzer", app_channel=0)
    assert canlib.xldriver.xlGetApplConfig.called


def test_set_application_config_mocked(mock_xldriver) -> None:
    canlib.xldriver.xlSetApplConfig = Mock()
    canlib.VectorBus.set_application_config(
        app_name="CANalyzer",
        app_channel=0,
        hw_type=xldefine.XL_HardwareType.XL_HWTYPE_VN1610,
        hw_index=0,
        hw_channel=0,
    )
    assert canlib.xldriver.xlSetApplConfig.called


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_set_and_get_application_config() -> None:
    xl_channel_config = _find_xl_channel_config(
        serial=_find_virtual_can_serial(), channel=1
    )
    canlib.VectorBus.set_application_config(
        app_name="python-can::test_vector",
        app_channel=5,
        hw_channel=xl_channel_config.hwChannel,
        hw_index=xl_channel_config.hwIndex,
        hw_type=xldefine.XL_HardwareType(xl_channel_config.hwType),
    )
    hw_type, hw_index, hw_channel = canlib.VectorBus.get_application_config(
        app_name="python-can::test_vector",
        app_channel=5,
    )
    assert hw_type == xldefine.XL_HardwareType(xl_channel_config.hwType)
    assert hw_index == xl_channel_config.hwIndex
    assert hw_channel == xl_channel_config.hwChannel


def test_set_timer_mocked(mock_xldriver) -> None:
    canlib.xldriver.xlSetTimerRate = Mock()
    bus = canlib.VectorBus(channel=0, bustype="vector", fd=True, _testing=True)
    bus.set_timer_rate(timer_rate_ms=1)
    assert canlib.xldriver.xlSetTimerRate.called


@pytest.mark.skipif(not XLDRIVER_FOUND, reason="Vector XL API is unavailable")
def test_set_timer() -> None:
    bus = canlib.VectorBus(
        channel=0, serial=_find_virtual_can_serial(), bustype="vector"
    )
    bus.handle_can_event = Mock()
    bus.set_timer_rate(timer_rate_ms=1)
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < 0.5:
        bus.recv(timeout=-1)

    # call_count is incorrect when using virtual bus
    # assert bus.handle_can_event.call_count > 498
    # assert bus.handle_can_event.call_count < 502


@pytest.mark.skipif(IS_WINDOWS, reason="Not relevant for Windows.")
def test_called_without_testing_argument() -> None:
    """This tests if an exception is thrown when we are not running on Windows."""
    with pytest.raises(can.CanInterfaceNotImplementedError):
        # do not set the _testing argument, since it would suppress the exception
        can.Bus(channel=0, bustype="vector")


def test_vector_error_pickle() -> None:
    for error_type in [
        VectorError,
        VectorInitializationError,
        VectorOperationError,
    ]:
        error_code = 118
        error_string = "XL_ERROR"
        function = "function_name"

        exc = error_type(error_code, error_string, function)

        # pickle and unpickle
        p = pickle.dumps(exc)
        exc_unpickled: VectorError = pickle.loads(p)

        assert str(exc) == str(exc_unpickled)
        assert error_code == exc_unpickled.error_code

        with pytest.raises(error_type):
            raise exc_unpickled


def test_vector_subtype_error_from_generic() -> None:
    for error_type in [VectorInitializationError, VectorOperationError]:
        error_code = 118
        error_string = "XL_ERROR"
        function = "function_name"

        generic = VectorError(error_code, error_string, function)

        # pickle and unpickle
        specific: VectorError = error_type.from_generic(generic)

        assert str(generic) == str(specific)
        assert error_code == specific.error_code

        with pytest.raises(error_type):
            raise specific


@pytest.mark.skipif(
    sys.byteorder != "little", reason="Test relies on little endian data."
)
def test_get_channel_configs() -> None:
    _original_func = canlib._get_xl_driver_config
    canlib._get_xl_driver_config = _get_predefined_xl_driver_config

    channel_configs = canlib.get_channel_configs()
    assert len(channel_configs) == 12

    canlib._get_xl_driver_config = _original_func


@pytest.mark.skipif(not IS_WINDOWS, reason="Windows specific test")
def test_winapi_availability() -> None:
    assert canlib.WaitForSingleObject is not None
    assert canlib.INFINITE is not None


def test_vector_channel_config_attributes():
    assert hasattr(VectorChannelConfig, "name")
    assert hasattr(VectorChannelConfig, "hw_type")
    assert hasattr(VectorChannelConfig, "hw_index")
    assert hasattr(VectorChannelConfig, "hw_channel")
    assert hasattr(VectorChannelConfig, "channel_index")
    assert hasattr(VectorChannelConfig, "channel_mask")
    assert hasattr(VectorChannelConfig, "channel_capabilities")
    assert hasattr(VectorChannelConfig, "channel_bus_capabilities")
    assert hasattr(VectorChannelConfig, "is_on_bus")
    assert hasattr(VectorChannelConfig, "bus_params")
    assert hasattr(VectorChannelConfig, "connected_bus_type")
    assert hasattr(VectorChannelConfig, "serial_number")
    assert hasattr(VectorChannelConfig, "article_number")
    assert hasattr(VectorChannelConfig, "transceiver_name")


def test_vector_bus_params_attributes():
    assert hasattr(VectorBusParams, "bus_type")
    assert hasattr(VectorBusParams, "can")
    assert hasattr(VectorBusParams, "canfd")


def test_vector_can_params_attributes():
    assert hasattr(VectorCanParams, "bitrate")
    assert hasattr(VectorCanParams, "sjw")
    assert hasattr(VectorCanParams, "tseg1")
    assert hasattr(VectorCanParams, "tseg2")
    assert hasattr(VectorCanParams, "sam")
    assert hasattr(VectorCanParams, "output_mode")
    assert hasattr(VectorCanParams, "can_op_mode")


def test_vector_canfd_params_attributes():
    assert hasattr(VectorCanFdParams, "bitrate")
    assert hasattr(VectorCanFdParams, "data_bitrate")
    assert hasattr(VectorCanFdParams, "sjw_abr")
    assert hasattr(VectorCanFdParams, "tseg1_abr")
    assert hasattr(VectorCanFdParams, "tseg2_abr")
    assert hasattr(VectorCanFdParams, "sam_abr")
    assert hasattr(VectorCanFdParams, "sjw_dbr")
    assert hasattr(VectorCanFdParams, "tseg1_dbr")
    assert hasattr(VectorCanFdParams, "tseg2_dbr")
    assert hasattr(VectorCanFdParams, "output_mode")
    assert hasattr(VectorCanFdParams, "can_op_mode")


# *****************************************************************************
#                           Utility functions
# *****************************************************************************


def _find_xl_channel_config(serial: int, channel: int) -> xlclass.XLchannelConfig:
    """Helper function"""
    xl_driver_config = xlclass.XLdriverConfig()
    canlib.xldriver.xlOpenDriver()
    canlib.xldriver.xlGetDriverConfig(xl_driver_config)
    canlib.xldriver.xlCloseDriver()

    for i in range(xl_driver_config.channelCount):
        xl_channel_config: xlclass.XLchannelConfig = xl_driver_config.channel[i]

        if xl_channel_config.serialNumber != serial:
            continue

        if xl_channel_config.hwChannel != channel:
            continue

        return xl_channel_config

    raise LookupError("XLchannelConfig not found.")


@functools.lru_cache()
def _find_virtual_can_serial() -> int:
    """Serial number might be 0 or 100 depending on driver version."""
    xl_driver_config = xlclass.XLdriverConfig()
    canlib.xldriver.xlOpenDriver()
    canlib.xldriver.xlGetDriverConfig(xl_driver_config)
    canlib.xldriver.xlCloseDriver()

    for i in range(xl_driver_config.channelCount):
        xl_channel_config: xlclass.XLchannelConfig = xl_driver_config.channel[i]

        if xl_channel_config.transceiverName.decode() == "Virtual CAN":
            return xl_channel_config.serialNumber

    raise LookupError("Vector virtual CAN not found")


XL_DRIVER_CONFIG_EXAMPLE = (
    b"\x0E\x00\x1E\x14\x0C\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61\x6E\x6E"
    b"\x65\x6C\x20\x53\x74\x72\x65\x61\x6D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x2D\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x04"
    b"\x0A\x40\x00\x02\x00\x02\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x04\x00\x00\x00\x00\x00\x00\x00\x8E"
    b"\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00\x00\x08"
    b"\x1C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39\x31"
    b"\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x31\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x01\x03\x02\x00\x00\x00\x00\x01\x02\x00\x00"
    b"\x00\x00\x00\x00\x00\x02\x10\x00\x08\x07\x01\x04\x00\x00\x00\x00\x00\x00\x04\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x04\x00"
    b"\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x46\x52\x70\x69\x67\x67\x79\x20\x31\x30"
    b"\x38\x30\x41\x6D\x61\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x05\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x32\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x02\x3C\x01\x00"
    b"\x00\x00\x00\x02\x04\x00\x00\x00\x00\x00\x00\x00\x12\x00\x00\xA2\x03\x05\x01\x00"
    b"\x00\x00\x04\x00\x00\x01\x00\x00\x00\x20\xA1\x07\x00\x01\x04\x03\x01\x01\x00\x00"
    b"\x00\x00\x00\x00\x00\x01\x80\x00\x00\x00\x68\x89\x09\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x0C\x00\x02\x0A\x04\x00\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00\x00\x00"
    b"\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x4F\x6E\x20"
    b"\x62\x6F\x61\x72\x64\x20\x43\x41\x4E\x20\x31\x30\x35\x31\x63\x61\x70\x28\x48\x69"
    b"\x67\x68\x73\x70\x65\x65\x64\x29\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03"
    b"\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61\x6E"
    b"\x6E\x65\x6C\x20\x33\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x2D\x00\x03\x3C\x01\x00\x00\x00\x00\x03\x08\x00\x00\x00\x00\x00\x00\x00\x12"
    b"\x00\x00\xA2\x03\x09\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x20\xA1\x07\x00"
    b"\x01\x04\x03\x01\x01\x00\x00\x00\x00\x00\x00\x00\x01\x9B\x00\x00\x00\x68\x89\x09"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x04\x00\x00\x00\x00\x00\x00\x00"
    b"\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00\x00"
    b"\x08\x1C\x00\x00\x4F\x6E\x20\x62\x6F\x61\x72\x64\x20\x43\x41\x4E\x20\x31\x30\x35"
    b"\x31\x63\x61\x70\x28\x48\x69\x67\x68\x73\x70\x65\x65\x64\x29\x00\x04\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39"
    b"\x31\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x34\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x04\x33\x01\x00\x00\x00\x00\x04\x10\x00"
    b"\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x03\x09\x02\x08\x00\x00\x00\x00\x00\x02"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x03"
    b"\x00\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x4C\x49\x4E\x70\x69\x67\x67\x79\x20"
    b"\x37\x32\x36\x39\x6D\x61\x67\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x07\x00\x00\x00\x70\x17\x00\x00\x0C\x09\x03\x04\x58\x02\x10\x0E\x30"
    b"\x57\x05\x00\x00\x00\x00\x00\x88\x13\x88\x13\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x35\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x05\x00\x00"
    b"\x00\x00\x02\x00\x05\x20\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x0C\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00\x00"
    b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61"
    b"\x6E\x6E\x65\x6C\x20\x36\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x2D\x00\x06\x00\x00\x00\x00\x02\x00\x06\x40\x00\x00\x00\x00\x00\x00\x00"
    b"\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00"
    b"\x00\x08\x1C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38"
    b"\x39\x31\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x37\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x07\x00\x00\x00\x00\x02\x00\x07\x80"
    b"\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x38"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x2D\x00\x08\x3C"
    b"\x01\x00\x00\x00\x00\x08\x00\x01\x00\x00\x00\x00\x00\x00\x12\x00\x00\xA2\x01\x00"
    b"\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x20\xA1\x07\x00\x01\x04\x03\x01\x01"
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x68\x89\x09\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x0C\x00\x02\x0A\x04\x00\x00\x00\x00\x00\x00\x00\x8E\x00\x02\x0A\x00"
    b"\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03\x00\x00\x08\x1C\x00\x00\x4F"
    b"\x6E\x20\x62\x6F\x61\x72\x64\x20\x43\x41\x4E\x20\x31\x30\x35\x31\x63\x61\x70\x28"
    b"\x48\x69\x67\x68\x73\x70\x65\x65\x64\x29\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x4E\x38\x39\x31\x34\x20\x43\x68"
    b"\x61\x6E\x6E\x65\x6C\x20\x39\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x2D\x00\x09\x80\x02\x00\x00\x00\x00\x09\x00\x02\x00\x00\x00\x00\x00"
    b"\x00\x02\x00\x00\x00\x40\x00\x40\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0C\x00\x02\x0A\x03\x00\x00\x00\x00\x00"
    b"\x00\x00\x8E\x00\x02\x0A\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xE9\x03"
    b"\x00\x00\x08\x1C\x00\x00\x44\x2F\x41\x20\x49\x4F\x70\x69\x67\x67\x79\x20\x38\x36"
    b"\x34\x32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x03\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x69"
    b"\x72\x74\x75\x61\x6C\x20\x43\x68\x61\x6E\x6E\x65\x6C\x20\x31\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x16\x00\x00\x00\x00\x00\x0A"
    b"\x00\x04\x00\x00\x00\x00\x00\x00\x07\x00\x00\xA0\x01\x00\x01\x00\x00\x00\x00\x00"
    b"\x00\x01\x00\x00\x00\x20\xA1\x07\x00\x01\x04\x03\x01\x01\x00\x00\x00\x00\x00\x00"
    b"\x00\x01\x00\x00\x00\x00\x68\x89\x09\x00\x00\x00\x00\x00\x00\x00\x00\x10\x00\x1E"
    b"\x14\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x56\x69\x72\x74\x75\x61\x6C"
    b"\x20\x43\x41\x4E\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x56\x69\x72\x74\x75\x61\x6C\x20\x43\x68\x61\x6E\x6E\x65\x6C"
    b"\x20\x32\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x01"
    b"\x16\x00\x00\x00\x00\x00\x0B\x00\x08\x00\x00\x00\x00\x00\x00\x07\x00\x00\xA0\x01"
    b"\x00\x01\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x20\xA1\x07\x00\x01\x04\x03\x01"
    b"\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x68\x89\x09\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x10\x00\x1E\x14\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x56\x69\x72\x74\x75\x61\x6C\x20\x43\x41\x4E\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x02" + 11832 * b"\x00"
)


def _get_predefined_xl_driver_config() -> xlclass.XLdriverConfig:
    return xlclass.XLdriverConfig.from_buffer_copy(XL_DRIVER_CONFIG_EXAMPLE)


# *****************************************************************************
#                       Mock functions/side effects
# *****************************************************************************


def xlGetApplConfig(
    app_name_p: ctypes.c_char_p,
    app_channel: ctypes.c_uint,
    hw_type: ctypes.POINTER(ctypes.c_uint),
    hw_index: ctypes.POINTER(ctypes.c_uint),
    hw_channel: ctypes.POINTER(ctypes.c_uint),
    bus_type: ctypes.c_uint,
) -> int:
    hw_type.value = 1
    hw_channel.value = 0
    return 0


def xlGetChannelIndex(
    hw_type: ctypes.c_int, hw_index: ctypes.c_int, hw_channel: ctypes.c_int
) -> int:
    return hw_channel


def xlOpenPort(
    port_handle_p: ctypes.POINTER(xlclass.XLportHandle),
    app_name_p: ctypes.c_char_p,
    access_mask: int,
    permission_mask: xlclass.XLaccess,
    rx_queue_size: ctypes.c_uint,
    xl_interface_version: ctypes.c_uint,
    bus_type: ctypes.c_uint,
) -> int:
    port_handle_p.value = 0
    permission_mask.value = access_mask
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

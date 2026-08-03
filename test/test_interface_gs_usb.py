"""Tests for the gs_usb interface."""

from unittest.mock import MagicMock, patch

import can
import pytest

from can.interfaces.gs_usb import (
    GsUsbBus,
    _find_gs_usb_devices,
)


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_devices_does_not_force_backend(mock_find):
    """Verify that _find_gs_usb_devices does not pass a backend argument,
    allowing pyusb to auto-detect the best available backend (WinUSB, libusbK, etc.)."""
    mock_find.return_value = []

    _find_gs_usb_devices()

    mock_find.assert_called_once()
    call_kwargs = mock_find.call_args[1]
    assert (
        "backend" not in call_kwargs
    ), "backend should not be specified so pyusb can auto-detect"
    assert call_kwargs["find_all"] is True


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_devices_with_args_does_not_force_backend(mock_find):
    """Verify that _find_gs_usb_devices with bus/address does not pass a backend argument."""
    mock_find.return_value = []

    _find_gs_usb_devices(bus=1, address=2)

    mock_find.assert_called_once()
    call_kwargs = mock_find.call_args[1]
    assert (
        "backend" not in call_kwargs
    ), "backend should not be specified so pyusb can auto-detect"
    assert call_kwargs["bus"] == 1
    assert call_kwargs["address"] == 2
    assert call_kwargs["find_all"] is True


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_devices_returns_raw_usb_devices(mock_find):
    """Verify that _find_gs_usb_devices returns the raw USB devices."""
    mock_dev1 = MagicMock()
    mock_dev2 = MagicMock()
    mock_find.return_value = [mock_dev1, mock_dev2]

    devices = _find_gs_usb_devices()

    assert len(devices) == 2
    assert devices[0] is mock_dev1
    assert devices[1] is mock_dev2


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_devices_returns_empty_list_when_no_devices(mock_find):
    """Verify that _find_gs_usb_devices returns an empty list when no devices are found."""
    mock_find.return_value = []

    devices = _find_gs_usb_devices()

    assert devices == []


@patch("can.interfaces.gs_usb.GsUsb")
@patch("can.interfaces.gs_usb._find_gs_usb_devices")
def test_send_dlc_zero_does_not_modify_message_data(mock_find_devices, mock_gs_usb_cls):
    """Verify that send() does not mutate msg.data when DLC < CAN_MAX_DLC."""
    mock_find_devices.return_value = [MagicMock()]
    mock_gs_usb = MagicMock()
    mock_gs_usb_cls.return_value = mock_gs_usb
    mock_gs_usb.device_capability.fclk_can = 48_000_000

    bus = GsUsbBus(channel=0, bitrate=500_000)
    msg = can.Message(arbitration_id=0x123, data=bytearray(), dlc=0)
    msg_data_copy = msg.data.copy()

    bus.send(msg)

    assert msg.data == msg_data_copy
    mock_gs_usb.send.assert_called_once()

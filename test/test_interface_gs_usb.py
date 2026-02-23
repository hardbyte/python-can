"""Tests for the gs_usb interface."""

from unittest.mock import MagicMock, patch

import pytest

from can.interfaces.gs_usb import (
    GsUsbBus,
    _find_gs_usb_device,
    _scan_gs_usb_devices,
)


@patch("can.interfaces.gs_usb.usb.core.find")
def test_scan_does_not_force_backend(mock_find):
    """Verify that _scan_gs_usb_devices does not pass a backend argument,
    allowing pyusb to auto-detect the best available backend (WinUSB, libusbK, etc.)."""
    mock_find.return_value = []

    _scan_gs_usb_devices()

    mock_find.assert_called_once()
    call_kwargs = mock_find.call_args[1]
    assert (
        "backend" not in call_kwargs
    ), "backend should not be specified so pyusb can auto-detect"
    assert call_kwargs["find_all"] is True


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_does_not_force_backend(mock_find):
    """Verify that _find_gs_usb_device does not pass a backend argument,
    allowing pyusb to auto-detect the best available backend (WinUSB, libusbK, etc.)."""
    mock_find.return_value = None

    _find_gs_usb_device(bus=1, address=2)

    mock_find.assert_called_once()
    call_kwargs = mock_find.call_args[1]
    assert (
        "backend" not in call_kwargs
    ), "backend should not be specified so pyusb can auto-detect"
    assert call_kwargs["bus"] == 1
    assert call_kwargs["address"] == 2


@patch("can.interfaces.gs_usb.usb.core.find")
def test_scan_returns_gs_usb_devices(mock_find):
    """Verify that _scan_gs_usb_devices wraps found USB devices in GsUsb objects."""
    mock_dev1 = MagicMock()
    mock_dev2 = MagicMock()
    mock_find.return_value = [mock_dev1, mock_dev2]

    devices = _scan_gs_usb_devices()

    assert len(devices) == 2
    assert devices[0].gs_usb is mock_dev1
    assert devices[1].gs_usb is mock_dev2


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_returns_gs_usb_device(mock_find):
    """Verify that _find_gs_usb_device wraps the found USB device in a GsUsb object."""
    mock_dev = MagicMock()
    mock_find.return_value = mock_dev

    device = _find_gs_usb_device(bus=1, address=2)

    assert device is not None
    assert device.gs_usb is mock_dev


@patch("can.interfaces.gs_usb.usb.core.find")
def test_find_returns_none_when_no_device(mock_find):
    """Verify that _find_gs_usb_device returns None when no device is found."""
    mock_find.return_value = None

    device = _find_gs_usb_device(bus=1, address=2)

    assert device is None


@patch("can.interfaces.gs_usb.usb.core.find")
def test_scan_returns_empty_list_when_no_devices(mock_find):
    """Verify that _scan_gs_usb_devices returns an empty list when no devices are found."""
    mock_find.return_value = []

    devices = _scan_gs_usb_devices()

    assert devices == []

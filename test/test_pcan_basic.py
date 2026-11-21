"""PCANBasic parameter marshalling without a driver or physical adapter."""

import ctypes
from unittest.mock import Mock

import pytest

from can.interfaces.pcan import basic


@pytest.mark.parametrize(
    "parameter,ctype,value",
    [
        (basic.PCAN_CHANNEL_CONDITION, ctypes.c_int, 3),
        (basic.PCAN_DEVICE_ID, ctypes.c_int, 42),
        (basic.PCAN_BUSOFF_AUTORESET, ctypes.c_int, 1),
        (basic.PCAN_ACCEPTANCE_FILTER_11BIT, ctypes.c_int64, 0x123456789ABCDEF),
        (basic.PCAN_ACCEPTANCE_FILTER_29BIT, ctypes.c_int64, 0x123456789ABCDEF),
        (basic.PCAN_TRACE_LOCATION, ctypes.c_char * 256, b"/tmp/can-traces"),
    ],
)
@pytest.mark.parametrize("operation", ["get", "set"])
def test_parameter_buffer_type(parameter, ctype, value, operation):
    api = basic.PCANBasic.__new__(basic.PCANBasic)
    driver = Mock()
    api._PCANBasic__m_dllBasic = driver

    def transfer(channel, requested_parameter, buffer, size):
        assert channel is basic.PCAN_USBBUS1
        assert requested_parameter is parameter
        assert size == ctypes.sizeof(ctype)
        typed = ctypes.cast(buffer, ctypes.POINTER(ctype)).contents
        if operation == "get":
            typed.value = value
        else:
            assert typed.value == value
        return basic.PCAN_ERROR_OK

    if operation == "get":
        driver.CAN_GetValue.side_effect = transfer
        status, result = api.GetValue(basic.PCAN_USBBUS1, parameter)
        assert result == value
        driver.CAN_GetValue.assert_called_once()
    else:
        driver.CAN_SetValue.side_effect = transfer
        status = api.SetValue(basic.PCAN_USBBUS1, parameter, value)
        driver.CAN_SetValue.assert_called_once()
    assert status == basic.PCAN_ERROR_OK

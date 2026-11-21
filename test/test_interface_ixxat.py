#!/usr/bin/env python

"""
Unittest for ixxat interface.

Includes mocked classic CAN and CAN FD timestamp regressions.

Run only this test:
python setup.py test --addopts "--verbose -s test/test_interface_ixxat.py"
"""

import ctypes
import time
import unittest
from collections import deque
from contextlib import nullcontext
from unittest.mock import Mock, patch

import pytest

import can
from can import ctypesutil

# Linux has no HRESULT; supply only the ABI scalar needed to import the wrappers.
# The DLL itself remains mocked and Windows driver support is not enabled.
with (
    nullcontext()
    if hasattr(ctypesutil, "HRESULT")
    else patch.object(ctypesutil, "HRESULT", ctypes.c_int32, create=True)
):
    from can.interfaces.ixxat import (
        canlib_vcinpl,
        canlib_vcinpl2,
        constants,
        structures,
    )


class SoftwareTestCase(unittest.TestCase):
    """
    Test cases that test the software only and do not rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", channel=0)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError:
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=-1)

        # rx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, rx_fifo_size=0)

        # tx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, tx_fifo_size=0)


class HardwareTestCase(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", channel=0)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError:
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        try:
            configs = can.detect_available_configs("ixxat")
            if configs:
                for interface_kwargs in configs:
                    bus = can.Bus(**interface_kwargs)
                    bus.shutdown()
            else:
                raise unittest.SkipTest("No adapters were detected")
        except can.CanInterfaceNotImplementedError:
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation_incorrect_channel(self):
        # non-existent channel -> use arbitrary high value
        with self.assertRaises(can.CanInitializationError):
            can.Bus(interface="ixxat", channel=0xFFFF)

    def test_send_after_shutdown(self):
        with can.Bus(interface="ixxat", channel=0) as bus:
            with self.assertRaises(can.CanOperationError):
                bus.send(can.Message(arbitration_id=0x3FF, dlc=0))


@pytest.fixture(params=[canlib_vcinpl, canlib_vcinpl2], ids=["classic", "fd"])
def backend(request):
    return request.param


def message(backend, kind, tick=0, first_byte=0, identifier=0):
    msg = structures.CANMSG2() if backend is canlib_vcinpl2 else structures.CANMSG()
    msg.uMsgInfo.Bits.type = kind
    msg.dwTime = tick
    msg.dwMsgId = identifier
    msg.abData[0] = first_byte
    if kind == constants.CAN_MSGTYPE_DATA:
        msg.uMsgInfo.Bits.dlc = 2
        msg.abData[1] = 0xBB
        if backend is canlib_vcinpl2:
            msg.uMsgInfo.Bits.edl = 1
            msg.uMsgInfo.Bits.fdr = 1
    return msg


@pytest.fixture
def open_bus(monkeypatch, backend):
    buses = []

    def create(startup=(), duration=0.25):
        pending = deque(startup)
        library = Mock()

        def capabilities(handle, pointer):
            caps = pointer._obj
            if backend is canlib_vcinpl2:
                caps.dwTscClkFreq = 1_000_000
            else:
                caps.dwClockFreq = 1_000_000
            caps.dwTscDivisor = 1

        def read(*args):
            if not pending:
                raise backend.VCIRxQueueEmptyError()
            msg = pending.popleft()
            ctypes.memmove(args[-1], ctypes.byref(msg), ctypes.sizeof(msg))

        library.canControlGetCaps.side_effect = capabilities
        library.canChannelReadMessage.side_effect = read
        library.canChannelPeekMessage.side_effect = read
        clock = Mock(wraps=time)
        clock.time.side_effect = [1_790_000_000.0, 1_790_000_000.0 + duration]
        monkeypatch.setattr(backend, "_canlib", library)
        monkeypatch.setattr(backend, "time", clock)
        bus = backend.IXXATBus(channel=0)
        buses.append(bus)
        return bus, pending

    yield create
    for bus in buses:
        bus.shutdown()


def receive(bus, timeout):
    # Classic returns after each INFO packet; FD may consume it internally.
    for _ in range(5):
        msg, _ = bus._recv_internal(timeout)
        if msg is not None:
            return msg
    pytest.fail("No data frame returned")


@pytest.mark.parametrize("duration", [0, 0.25])
def test_epoch_is_midpoint_of_controller_start(backend, open_bus, duration):
    bus, pending = open_bus(duration=duration)
    pending.append(
        message(backend, constants.CAN_MSGTYPE_DATA, first_byte=0xAA, identifier=0x123)
    )
    msg = receive(bus, 0.1)
    assert msg.timestamp == pytest.approx(1_790_000_000 + duration / 2, abs=1e-6, rel=0)
    assert msg.arbitration_id == 0x123
    assert msg.data == bytes.fromhex("AABB")
    assert msg.is_fd == (backend is canlib_vcinpl2)
    assert msg.bitrate_switch == (backend is canlib_vcinpl2)


@pytest.mark.parametrize("rollover", [False, True])
def test_startup_drain_preserves_timestamp_metadata(backend, open_bus, rollover):
    start = 0xFFFFFFF0 if rollover else 100_000_000
    startup = [
        message(backend, constants.CAN_MSGTYPE_INFO, start, constants.CAN_INFO_START)
    ]
    if rollover:
        startup.append(message(backend, constants.CAN_MSGTYPE_TIMEOVR, identifier=1))
    bus, pending = open_bus(startup)
    tick = 0x20 if rollover else start + 1_234_567
    pending.append(message(backend, constants.CAN_MSGTYPE_DATA, tick))
    elapsed = 0.000048 if rollover else 1.234567
    assert receive(bus, 0.1).timestamp == pytest.approx(
        1_790_000_000.125 + elapsed, abs=1e-6, rel=0
    )


@pytest.mark.parametrize("timeout", [0, 0.1])
def test_received_start_tick_preserves_frame_spacing(backend, open_bus, timeout):
    bus, pending = open_bus()
    # Isolate received clock metadata from the independently tested epoch calculation.
    bus._timeoffset = 1_790_000_000.125
    pending.extend(
        [
            message(
                backend,
                constants.CAN_MSGTYPE_INFO,
                100_000_000,
                constants.CAN_INFO_START,
            ),
            message(backend, constants.CAN_MSGTYPE_DATA, 101_234_567),
            message(backend, constants.CAN_MSGTYPE_DATA, 102_469_134),
        ]
    )
    first = receive(bus, timeout)
    second = receive(bus, timeout)
    assert first.timestamp == pytest.approx(1_790_000_001.359567, abs=1e-6, rel=0)
    assert second.timestamp - first.timestamp == pytest.approx(
        1.234567, abs=1e-6, rel=0
    )


@pytest.mark.parametrize("timeout", [0, 0.1])
def test_overrun_with_start_byte_is_not_mistaken_for_start(backend, open_bus, timeout):
    bus, pending = open_bus()
    bus._timeoffset = 1_790_000_000.125
    bus._starttickoffset = 0xFFFFFFF0
    pending.extend(
        [
            message(
                backend, constants.CAN_MSGTYPE_TIMEOVR, 7, constants.CAN_INFO_START, 1
            ),
            message(backend, constants.CAN_MSGTYPE_DATA, 0x20),
        ]
    )
    assert receive(bus, timeout).timestamp == pytest.approx(
        1_790_000_000.125048, abs=1e-6, rel=0
    )


@pytest.mark.parametrize("timeout", [0, 0.1])
def test_unrelated_info_does_not_change_clock(backend, open_bus, timeout):
    bus, pending = open_bus()
    bus._timeoffset = 1_790_000_000.125
    pending.extend(
        [
            message(
                backend,
                constants.CAN_MSGTYPE_INFO,
                500_000_000,
                constants.CAN_INFO_STOP,
            ),
            message(backend, constants.CAN_MSGTYPE_DATA, 1_000_000),
        ]
    )
    assert receive(bus, timeout).timestamp == pytest.approx(
        1_790_000_001.125, abs=1e-6, rel=0
    )


def test_error_byte_is_not_interpreted_as_start(backend, open_bus, caplog):
    bus, pending = open_bus()
    bus._timeoffset = 1_790_000_000.125
    pending.extend(
        [
            message(
                backend,
                constants.CAN_MSGTYPE_ERROR,
                500_000_000,
                constants.CAN_ERROR_STUFF,
            ),
            message(backend, constants.CAN_MSGTYPE_DATA, 1_000_000),
        ]
    )
    assert receive(bus, 0.1).timestamp == pytest.approx(
        1_790_000_001.125, abs=1e-6, rel=0
    )
    assert "CAN bit stuff error" in caplog.text


if __name__ == "__main__":
    unittest.main()

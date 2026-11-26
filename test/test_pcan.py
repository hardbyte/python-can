"""
Test for PCAN Interface
"""

import ctypes
import importlib.util
import struct
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest import mock
from unittest.mock import Mock, patch

import pytest
from parameterized import parameterized

import can
from can import BusState, CanProtocol
from can.exceptions import CanInitializationError
from can.interfaces.pcan import PcanBus, PcanError, basic
from can.interfaces.pcan import pcan as pcan_module
from can.interfaces.pcan.basic import *


class TestPCANBus(unittest.TestCase):
    def setUp(self) -> None:
        patcher = mock.patch("can.interfaces.pcan.pcan.PCANBasic", spec=True)
        self.MockPCANBasic = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock_pcan = self.MockPCANBasic.return_value
        self.mock_pcan.Initialize.return_value = PCAN_ERROR_OK
        self.mock_pcan.InitializeFD = Mock(return_value=PCAN_ERROR_OK)
        self.mock_pcan.SetValue = Mock(return_value=PCAN_ERROR_OK)
        self.mock_pcan.GetValue = self._mockGetValue
        self.PCAN_API_VERSION_SIM = "4.2"
        self.bus = None

    def tearDown(self) -> None:
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def _mockGetValue(self, channel, parameter):
        """
        This method is used as mock for GetValue method of PCANBasic object.
        Only a subset of parameters are supported.
        """
        if parameter == PCAN_API_VERSION:
            return PCAN_ERROR_OK, self.PCAN_API_VERSION_SIM.encode("ascii")
        elif parameter == PCAN_RECEIVE_EVENT:
            return PCAN_ERROR_OK, int.from_bytes(PCAN_RECEIVE_EVENT, "big")
        raise NotImplementedError(
            f"No mock return value specified for parameter {parameter}"
        )

    def test_bus_creation(self) -> None:
        self.bus = can.Bus(interface="pcan")

        self.assertIsInstance(self.bus, PcanBus)
        self.assertEqual(self.bus.protocol, CanProtocol.CAN_20)

        with pytest.deprecated_call():
            self.assertFalse(self.bus.fd)

        self.MockPCANBasic.assert_called_once()
        self.mock_pcan.Initialize.assert_called_once()
        self.mock_pcan.InitializeFD.assert_not_called()

    def test_bus_creation_state_error(self) -> None:
        with self.assertRaises(ValueError):
            can.Bus(interface="pcan", state=BusState.ERROR)

    @parameterized.expand([("f_clock", 80_000_000), ("f_clock_mhz", 80)])
    def test_bus_creation_fd(self, clock_param: str, clock_val: int) -> None:
        self.bus = can.Bus(
            interface="pcan",
            fd=True,
            nom_brp=1,
            nom_tseg1=129,
            nom_tseg2=30,
            nom_sjw=1,
            data_brp=1,
            data_tseg1=9,
            data_tseg2=6,
            data_sjw=1,
            channel="PCAN_USBBUS1",
            **{clock_param: clock_val},
        )

        self.assertIsInstance(self.bus, PcanBus)
        self.assertEqual(self.bus.protocol, CanProtocol.CAN_FD)

        with pytest.deprecated_call():
            self.assertTrue(self.bus.fd)

        self.MockPCANBasic.assert_called_once()
        self.mock_pcan.Initialize.assert_not_called()
        self.mock_pcan.InitializeFD.assert_called_once()

        # Retrieve second argument of first call
        bitrate_arg = self.mock_pcan.InitializeFD.call_args[0][-1]

        self.assertTrue(f"{clock_param}={clock_val}".encode("ascii") in bitrate_arg)
        self.assertTrue(b"nom_brp=1" in bitrate_arg)
        self.assertTrue(b"nom_tseg1=129" in bitrate_arg)
        self.assertTrue(b"nom_tseg2=30" in bitrate_arg)
        self.assertTrue(b"nom_sjw=1" in bitrate_arg)
        self.assertTrue(b"data_brp=1" in bitrate_arg)
        self.assertTrue(b"data_tseg1=9" in bitrate_arg)
        self.assertTrue(b"data_tseg2=6" in bitrate_arg)
        self.assertTrue(b"data_sjw=1" in bitrate_arg)

    def test_api_version_low(self) -> None:
        self.PCAN_API_VERSION_SIM = "1.0"
        with self.assertLogs("can.pcan", level="WARNING") as cm:
            self.bus = can.Bus(interface="pcan")
            found_version_warning = False
            for i in cm.output:
                if "version" in i and "pcan" in i:
                    found_version_warning = True
            self.assertTrue(
                found_version_warning,
                f"No warning was logged for incompatible api version {cm.output}",
            )

    def test_api_version_read_fail(self) -> None:
        self.mock_pcan.GetValue = Mock(return_value=(PCAN_ERROR_ILLOPERATION, None))
        with self.assertRaises(CanInitializationError):
            self.bus = can.Bus(interface="pcan")

    def test_issue1642(self) -> None:
        self.PCAN_API_VERSION_SIM = "1, 3, 0, 50"
        with self.assertLogs("can.pcan", level="WARNING") as cm:
            self.bus = can.Bus(interface="pcan")
            found_version_warning = False
            for i in cm.output:
                if "version" in i and "pcan" in i:
                    found_version_warning = True
            self.assertTrue(
                found_version_warning,
                f"No warning was logged for incompatible api version {cm.output}",
            )

    @parameterized.expand(
        [
            ("no_error", PCAN_ERROR_OK, PCAN_ERROR_OK, "some ok text 1"),
            ("one_error", PCAN_ERROR_UNKNOWN, PCAN_ERROR_OK, "some ok text 2"),
            (
                "both_errors",
                PCAN_ERROR_UNKNOWN,
                PCAN_ERROR_UNKNOWN,
                "An error occurred. Error-code's text (8h) couldn't be retrieved",
            ),
        ]
    )
    def test_get_formatted_error(self, name, status1, status2, expected_result: str):
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan")
            self.mock_pcan.GetErrorText = Mock(
                side_effect=[
                    (status1, expected_result.encode("utf-8", errors="replace")),
                    (status2, expected_result.encode("utf-8", errors="replace")),
                ]
            )

            complete_text = self.bus._get_formatted_error(PCAN_ERROR_BUSHEAVY)

            self.assertEqual(complete_text, expected_result)

    def test_status(self) -> None:
        self.bus = can.Bus(interface="pcan")
        self.bus.status()
        self.mock_pcan.GetStatus.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, True), ("error", PCAN_ERROR_UNKNOWN, False)]
    )
    def test_status_is_ok(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.mock_pcan.GetStatus = Mock(return_value=status)
            self.bus = can.Bus(interface="pcan")
            self.assertEqual(self.bus.status_is_ok(), expected_result)
            self.mock_pcan.GetStatus.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, True), ("error", PCAN_ERROR_UNKNOWN, False)]
    )
    def test_reset(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.mock_pcan.Reset = Mock(return_value=status)
            self.bus = can.Bus(interface="pcan", fd=True)
            self.assertEqual(self.bus.reset(), expected_result)
            self.mock_pcan.Reset.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, 1), ("error", PCAN_ERROR_UNKNOWN, None)]
    )
    def test_get_device_number(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan", fd=True)
            # Mock GetValue after creation of bus to use first mock of
            # GetValue in constructor
            self.mock_pcan.GetValue = Mock(return_value=(status, 1))

            self.assertEqual(self.bus.get_device_number(), expected_result)
            self.mock_pcan.GetValue.assert_called_once_with(
                PCAN_USBBUS1, PCAN_DEVICE_NUMBER
            )

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, True), ("error", PCAN_ERROR_UNKNOWN, False)]
    )
    def test_set_device_number(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan")
            self.mock_pcan.SetValue = Mock(return_value=status)
            self.assertEqual(self.bus.set_device_number(3), expected_result)
            # check last SetValue call
            self.assertEqual(
                self.mock_pcan.SetValue.call_args_list[-1][0],
                (PCAN_USBBUS1, PCAN_DEVICE_NUMBER, 3),
            )

    def test_recv(self):
        data = (ctypes.c_ubyte * 8)(*[x for x in range(8)])
        msg = TPCANMsg(ID=0xC0FFEF, LEN=8, MSGTYPE=PCAN_MESSAGE_EXTENDED, DATA=data)

        timestamp = TPCANTimestamp()
        self.mock_pcan.Read = Mock(return_value=(PCAN_ERROR_OK, msg, timestamp))
        with patch.object(pcan_module, "boottimeEpoch", 0):
            self.bus = can.Bus(interface="pcan")
            recv_msg = self.bus.recv()
        self.assertEqual(recv_msg.arbitration_id, msg.ID)
        self.assertEqual(recv_msg.dlc, msg.LEN)
        self.assertEqual(recv_msg.is_extended_id, True)
        self.assertEqual(recv_msg.is_fd, False)
        self.assertSequenceEqual(recv_msg.data, msg.DATA)
        self.assertEqual(recv_msg.timestamp, 0)
        self.assertEqual(recv_msg.channel, "PCAN_USBBUS1")

    def test_recv_fd(self):
        data = (ctypes.c_ubyte * 64)(*[x for x in range(64)])
        msg = TPCANMsgFD(
            ID=0xC0FFEF,
            DLC=64,
            MSGTYPE=(PCAN_MESSAGE_EXTENDED.value | PCAN_MESSAGE_FD.value),
            DATA=data,
        )

        timestamp = TPCANTimestampFD()

        self.mock_pcan.ReadFD = Mock(return_value=(PCAN_ERROR_OK, msg, timestamp))

        with patch.object(pcan_module, "boottimeEpoch", 0):
            self.bus = can.Bus(interface="pcan", fd=True)
            recv_msg = self.bus.recv()
        self.assertEqual(recv_msg.arbitration_id, msg.ID)
        self.assertEqual(recv_msg.dlc, msg.DLC)
        self.assertEqual(recv_msg.is_extended_id, True)
        self.assertEqual(recv_msg.is_fd, True)
        self.assertSequenceEqual(recv_msg.data, msg.DATA)
        self.assertEqual(recv_msg.timestamp, 0)
        self.assertEqual(recv_msg.channel, "PCAN_USBBUS1")

    @parameterized.expand([("classic", False), ("fd", True)])
    def test_recv_skips_status_frames(self, name, fd):
        if fd:
            status = TPCANMsgFD(ID=1, DLC=4, MSGTYPE=PCAN_MESSAGE_STATUS.value)
            data = TPCANMsgFD(ID=1, DLC=1, MSGTYPE=PCAN_MESSAGE_FD.value)
            timestamp = TPCANTimestampFD()
            read = self.mock_pcan.ReadFD
        else:
            status = TPCANMsg(ID=1, LEN=4, MSGTYPE=PCAN_MESSAGE_STATUS.value)
            data = TPCANMsg(ID=1, LEN=1, MSGTYPE=PCAN_MESSAGE_STANDARD.value)
            timestamp = TPCANTimestamp()
            read = self.mock_pcan.Read
        data.DATA[0] = 0xAB
        read.side_effect = [
            (PCAN_ERROR_OK, status, timestamp),
            (PCAN_ERROR_OK, data, timestamp),
            (PCAN_ERROR_OK, status, timestamp),
            (PCAN_ERROR_QRCVEMPTY, type(status)(), timestamp),
        ]
        self.bus = can.Bus(interface="pcan", fd=fd)

        recv_msg = self.bus.recv(timeout=0)
        self.assertIsNotNone(recv_msg)
        self.assertEqual(recv_msg.arbitration_id, 1)
        self.assertEqual(recv_msg.is_fd, fd)
        self.assertSequenceEqual(recv_msg.data, [0xAB])
        self.assertIsNone(self.bus.recv(timeout=0))

    def _load_timestamp_backend(self, linux: bool, windows: bool) -> ModuleType:
        # The platform choice is made at import time; use a separate namespace.
        spec = importlib.util.spec_from_file_location(
            "can.interfaces.pcan._timestamp_test", pcan_module.__file__
        )
        assert spec is not None and spec.loader is not None
        backend = importlib.util.module_from_spec(spec)
        get_tick_count = Mock(return_value=100_000_000)
        get_tick_count.restype = ctypes.c_ulonglong
        fake_windll = SimpleNamespace(
            kernel32=SimpleNamespace(GetTickCount64=get_tick_count)
        )

        with patch.dict(sys.modules):
            sys.modules.pop("uptime", None)
            with (
                patch("can.interfaces.pcan.basic.IS_LINUX", linux),
                patch("can.interfaces.pcan.basic.IS_WINDOWS", windows),
                patch.object(ctypes, "windll", fake_windll, create=True),
                patch("time.time", return_value=1_700_100_000),
            ):
                spec.loader.exec_module(backend)
        return backend

    @parameterized.expand(
        [
            ("linux_classic", True, False),
            ("linux_fd", True, True),
            ("windows_classic", False, False),
        ]
    )
    def test_timestamp_clock(self, name: str, linux: bool, fd: bool) -> None:
        backend = self._load_timestamp_backend(linux, windows=not linux)
        backend.HAS_EVENTS = False
        with patch.object(backend, "PCANBasic", return_value=self.mock_pcan):
            self.bus = backend.PcanBus(fd=fd)

        # Linux timestamps are epoch microseconds, not boot-relative.
        raw_us = 1_790_000_000_123_456 if linux else 123_456
        if fd:
            self.mock_pcan.ReadFD.return_value = (
                PCAN_ERROR_OK,
                TPCANMsgFD(
                    ID=0x123,
                    DLC=9,
                    MSGTYPE=PCAN_MESSAGE_FD.value,
                    DATA=(ctypes.c_ubyte * 64)(),
                ),
                TPCANTimestampFD(raw_us),
            )
        else:
            millis, micros = divmod(raw_us, 1000)
            overflow, millis = divmod(millis, 1 << 32)
            self.mock_pcan.Read.return_value = (
                PCAN_ERROR_OK,
                TPCANMsg(
                    ID=0x123,
                    LEN=1,
                    MSGTYPE=PCAN_MESSAGE_STANDARD,
                    DATA=(ctypes.c_ubyte * 8)(),
                ),
                TPCANTimestamp(millis=millis, millis_overflow=overflow, micros=micros),
            )
        msg = self.bus.recv(timeout=0)
        self.assertIsNotNone(msg)
        expected_offset = 0 if linux else 1_700_000_000
        self.assertAlmostEqual(
            msg.timestamp, expected_offset + raw_us / 1_000_000, places=6
        )

    @pytest.mark.timeout(3.0)
    @patch("select.select", return_value=([], [], []))
    def test_recv_no_message(self, mock_select):
        self.mock_pcan.Read = Mock(return_value=(PCAN_ERROR_QRCVEMPTY, None, None))
        self.bus = can.Bus(interface="pcan")
        self.assertEqual(self.bus.recv(timeout=0.5), None)

    def test_send(self) -> None:
        self.mock_pcan.Write = Mock(return_value=PCAN_ERROR_OK)
        self.bus = can.Bus(interface="pcan")
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        self.mock_pcan.Write.assert_called_once()
        self.mock_pcan.WriteFD.assert_not_called()

    def test_send_fd(self) -> None:
        self.mock_pcan.WriteFD = Mock(return_value=PCAN_ERROR_OK)
        self.bus = can.Bus(interface="pcan", fd=True)
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        self.mock_pcan.Write.assert_not_called()
        self.mock_pcan.WriteFD.assert_called_once()

    @parameterized.expand(
        [
            (
                "standart",
                (False, False, False, False, False, False),
                PCAN_MESSAGE_STANDARD,
            ),
            (
                "extended",
                (True, False, False, False, False, False),
                PCAN_MESSAGE_EXTENDED,
            ),
            ("remote", (False, True, False, False, False, False), PCAN_MESSAGE_RTR),
            ("error", (False, False, True, False, False, False), PCAN_MESSAGE_ERRFRAME),
            ("fd", (False, False, False, True, False, False), PCAN_MESSAGE_FD),
            (
                "bitrate_switch",
                (False, False, False, False, True, False),
                PCAN_MESSAGE_BRS,
            ),
            (
                "error_state_indicator",
                (False, False, False, False, False, True),
                PCAN_MESSAGE_ESI,
            ),
        ]
    )
    def test_send_type(self, name, msg_type, expected_value) -> None:
        with self.subTest(name):
            (
                is_extended_id,
                is_remote_frame,
                is_error_frame,
                is_fd,
                bitrate_switch,
                error_state_indicator,
            ) = msg_type

            self.mock_pcan.Write = Mock(return_value=PCAN_ERROR_OK)

            self.bus = can.Bus(interface="pcan")
            msg = can.Message(
                arbitration_id=0xC0FFEF,
                data=[1, 2, 3, 4, 5, 6, 7, 8],
                is_extended_id=is_extended_id,
                is_remote_frame=is_remote_frame,
                is_error_frame=is_error_frame,
                bitrate_switch=bitrate_switch,
                error_state_indicator=error_state_indicator,
                is_fd=is_fd,
            )
            self.bus.send(msg)
            # self.mock_m_objPCANBasic.Write.assert_called_once()
            CANMsg = self.mock_pcan.Write.call_args_list[0][0][1]
            self.assertEqual(CANMsg.MSGTYPE, expected_value.value)

    def test_send_error(self) -> None:
        self.mock_pcan.Write = Mock(return_value=PCAN_ERROR_BUSHEAVY)
        self.bus = can.Bus(interface="pcan")
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )

        with self.assertRaises(PcanError):
            self.bus.send(msg)

    @parameterized.expand([("on", True), ("off", False)])
    def test_flash(self, name, flash) -> None:
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan")
            self.bus.flash(flash)
            call_list = self.mock_pcan.SetValue.call_args_list
            last_call_args_list = call_list[-1][0]
            self.assertEqual(
                last_call_args_list, (PCAN_USBBUS1, PCAN_CHANNEL_IDENTIFYING, flash)
            )

    def test_shutdown(self) -> None:
        self.bus = can.Bus(interface="pcan")
        self.bus.shutdown()
        self.mock_pcan.Uninitialize.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [
            ("active", BusState.ACTIVE, PCAN_PARAMETER_OFF),
            ("passive", BusState.PASSIVE, PCAN_PARAMETER_ON),
        ]
    )
    def test_state(self, name, bus_state: BusState, expected_parameter) -> None:
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan")

            self.bus.state = bus_state
            call_list = self.mock_pcan.SetValue.call_args_list
            last_call_args_list = call_list[-1][0]
            self.assertEqual(
                last_call_args_list,
                (PCAN_USBBUS1, PCAN_LISTEN_ONLY, expected_parameter),
            )

    def test_state_constructor(self):
        for state in [BusState.ACTIVE, BusState.PASSIVE]:
            bus = can.Bus(interface="pcan", state=state)
            assert bus.state == state

    def test_detect_available_configs(self) -> None:
        if platform.system() == "Darwin":
            self.mock_pcan.GetValue = Mock(
                return_value=(PCAN_ERROR_OK, PCAN_CHANNEL_AVAILABLE)
            )
            configs = PcanBus._detect_available_configs()
            self.assertEqual(len(configs), 50)
        else:
            value = (TPCANChannelInformation * 1).from_buffer_copy(
                struct.pack("HBBI33sII", 81, 5, 0, 1, b"PCAN-USB FD", 1122867, 1)
            )
            self.mock_pcan.GetValue = Mock(return_value=(PCAN_ERROR_OK, value))
            configs = PcanBus._detect_available_configs()
            assert len(configs) == 1
            assert configs[0]["interface"] == "pcan"
            assert configs[0]["channel"] == "PCAN_USBBUS1"
            assert configs[0]["supports_fd"]
            assert configs[0]["controller_number"] == 0
            assert configs[0]["device_features"] == 1
            assert configs[0]["device_id"] == 1122867
            assert configs[0]["device_name"] == "PCAN-USB FD"
            assert configs[0]["device_type"] == 5
            assert configs[0]["channel_condition"] == 1

    @parameterized.expand([("valid", PCAN_ERROR_OK, "OK"), ("invalid", 0x00005, None)])
    def test_status_string(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.bus = can.Bus(interface="pcan")
            self.mock_pcan.GetStatus = Mock(return_value=status)
            self.assertEqual(self.bus.status_string(), expected_result)
            self.mock_pcan.GetStatus.assert_called()

    @parameterized.expand([(0x0, "error"), (0x42, "PCAN_USBBUS8")])
    def test_constructor_with_device_id(self, dev_id, expected_result):
        def get_value_side_effect(handle, param):
            if param == PCAN_API_VERSION:
                return PCAN_ERROR_OK, self.PCAN_API_VERSION_SIM.encode("ascii")

            if handle in (PCAN_USBBUS8, PCAN_USBBUS14):
                return 0, 0x42
            else:
                return PCAN_ERROR_ILLHW, 0x0

        self.mock_pcan.GetValue = Mock(side_effect=get_value_side_effect)

        if expected_result == "error":
            with self.assertRaises(ValueError):
                can.Bus(interface="pcan", device_id=dev_id)
        else:
            self.bus = can.Bus(interface="pcan", device_id=dev_id)
            self.assertEqual(expected_result, self.bus.channel_info)

    def test_bus_creation_auto_reset(self):
        self.bus = can.Bus(interface="pcan", auto_reset=True)
        self.assertIsInstance(self.bus, PcanBus)
        self.MockPCANBasic.assert_called_once()

    def test_auto_reset_init_fault(self):
        self.mock_pcan.SetValue = Mock(return_value=PCAN_ERROR_INITIALIZE)
        with self.assertRaises(CanInitializationError):
            self.bus = can.Bus(interface="pcan", auto_reset=True)

    def test_peak_fd_bus_constructor_regression(self):
        # Tests that the following issue has been fixed:
        # https://github.com/hardbyte/python-can/issues/1458
        params = {
            "interface": "pcan",
            "fd": True,
            "f_clock": 80000000,
            "nom_brp": 1,
            "nom_tseg1": 129,
            "nom_tseg2": 30,
            "nom_sjw": 1,
            "data_brp": 1,
            "data_tseg1": 9,
            "data_tseg2": 6,
            "data_sjw": 1,
            "channel": "PCAN_USBBUS1",
        }

        can.Bus(**params)

    def test_constructor_bit_timing(self):
        timing = can.BitTiming.from_registers(f_clock=8_000_000, btr0=0x47, btr1=0x2F)
        bus = can.Bus(interface="pcan", channel="PCAN_USBBUS1", timing=timing)

        bitrate_arg = self.mock_pcan.Initialize.call_args[0][1]
        self.assertEqual(bitrate_arg.value, 0x472F)
        self.assertEqual(bus.protocol, CanProtocol.CAN_20)

    def test_constructor_bit_timing_fd(self):
        timing = can.BitTimingFd(
            f_clock=40_000_000,
            nom_brp=1,
            nom_tseg1=129,
            nom_tseg2=30,
            nom_sjw=1,
            data_brp=1,
            data_tseg1=9,
            data_tseg2=6,
            data_sjw=1,
        )
        bus = can.Bus(interface="pcan", channel="PCAN_USBBUS1", timing=timing)
        self.assertEqual(bus.protocol, CanProtocol.CAN_FD)

        bitrate_arg = self.mock_pcan.InitializeFD.call_args[0][-1]

        self.assertTrue(b"f_clock=40000000" in bitrate_arg)
        self.assertTrue(b"nom_brp=1" in bitrate_arg)
        self.assertTrue(b"nom_tseg1=129" in bitrate_arg)
        self.assertTrue(b"nom_tseg2=30" in bitrate_arg)
        self.assertTrue(b"nom_sjw=1" in bitrate_arg)
        self.assertTrue(b"data_brp=1" in bitrate_arg)
        self.assertTrue(b"data_tseg1=9" in bitrate_arg)
        self.assertTrue(b"data_tseg2=6" in bitrate_arg)
        self.assertTrue(b"data_sjw=1" in bitrate_arg)


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


if __name__ == "__main__":
    unittest.main()

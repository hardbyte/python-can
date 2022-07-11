"""
Test for PCAN Interface
"""

import ctypes
import unittest
from unittest import mock
from unittest.mock import Mock

import pytest
from parameterized import parameterized

import can
from can.bus import BusState
from can.exceptions import CanInitializationError
from can.interfaces.pcan.basic import *
from can.interfaces.pcan import PcanBus, PcanError


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
        raise NotImplementedError(
            f"No mock return value specified for parameter {parameter}"
        )

    def test_bus_creation(self) -> None:
        self.bus = can.Bus(bustype="pcan")
        self.assertIsInstance(self.bus, PcanBus)
        self.MockPCANBasic.assert_called_once()
        self.mock_pcan.Initialize.assert_called_once()
        self.mock_pcan.InitializeFD.assert_not_called()

    def test_bus_creation_state_error(self) -> None:
        with self.assertRaises(ValueError):
            can.Bus(bustype="pcan", state=BusState.ERROR)

    def test_bus_creation_fd(self) -> None:
        self.bus = can.Bus(bustype="pcan", fd=True)
        self.assertIsInstance(self.bus, PcanBus)
        self.MockPCANBasic.assert_called_once()
        self.mock_pcan.Initialize.assert_not_called()
        self.mock_pcan.InitializeFD.assert_called_once()

    def test_api_version_low(self) -> None:
        self.PCAN_API_VERSION_SIM = "1.0"
        with self.assertLogs("can.pcan", level="WARNING") as cm:
            self.bus = can.Bus(bustype="pcan")
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
            self.bus = can.Bus(bustype="pcan")

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
            self.bus = can.Bus(bustype="pcan")
            self.mock_pcan.GetErrorText = Mock(
                side_effect=[
                    (status1, expected_result.encode("utf-8", errors="replace")),
                    (status2, expected_result.encode("utf-8", errors="replace")),
                ]
            )

            complete_text = self.bus._get_formatted_error(PCAN_ERROR_BUSHEAVY)

            self.assertEqual(complete_text, expected_result)

    def test_status(self) -> None:
        self.bus = can.Bus(bustype="pcan")
        self.bus.status()
        self.mock_pcan.GetStatus.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, True), ("error", PCAN_ERROR_UNKNOWN, False)]
    )
    def test_status_is_ok(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.mock_pcan.GetStatus = Mock(return_value=status)
            self.bus = can.Bus(bustype="pcan")
            self.assertEqual(self.bus.status_is_ok(), expected_result)
            self.mock_pcan.GetStatus.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, True), ("error", PCAN_ERROR_UNKNOWN, False)]
    )
    def test_reset(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.mock_pcan.Reset = Mock(return_value=status)
            self.bus = can.Bus(bustype="pcan", fd=True)
            self.assertEqual(self.bus.reset(), expected_result)
            self.mock_pcan.Reset.assert_called_once_with(PCAN_USBBUS1)

    @parameterized.expand(
        [("no_error", PCAN_ERROR_OK, 1), ("error", PCAN_ERROR_UNKNOWN, None)]
    )
    def test_get_device_number(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.bus = can.Bus(bustype="pcan", fd=True)
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
            self.bus = can.Bus(bustype="pcan")
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
        self.bus = can.Bus(bustype="pcan")

        recv_msg = self.bus.recv()
        self.assertEqual(recv_msg.arbitration_id, msg.ID)
        self.assertEqual(recv_msg.dlc, msg.LEN)
        self.assertEqual(recv_msg.is_extended_id, True)
        self.assertEqual(recv_msg.is_fd, False)
        self.assertSequenceEqual(recv_msg.data, msg.DATA)
        self.assertEqual(recv_msg.timestamp, 0)

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

        self.bus = can.Bus(bustype="pcan", fd=True)

        recv_msg = self.bus.recv()
        self.assertEqual(recv_msg.arbitration_id, msg.ID)
        self.assertEqual(recv_msg.dlc, msg.DLC)
        self.assertEqual(recv_msg.is_extended_id, True)
        self.assertEqual(recv_msg.is_fd, True)
        self.assertSequenceEqual(recv_msg.data, msg.DATA)
        self.assertEqual(recv_msg.timestamp, 0)

    @pytest.mark.timeout(3.0)
    def test_recv_no_message(self):
        self.mock_pcan.Read = Mock(return_value=(PCAN_ERROR_QRCVEMPTY, None, None))
        self.bus = can.Bus(bustype="pcan")
        self.assertEqual(self.bus.recv(timeout=0.5), None)

    def test_send(self) -> None:
        self.mock_pcan.Write = Mock(return_value=PCAN_ERROR_OK)
        self.bus = can.Bus(bustype="pcan")
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )
        self.bus.send(msg)
        self.mock_pcan.Write.assert_called_once()
        self.mock_pcan.WriteFD.assert_not_called()

    def test_send_fd(self) -> None:
        self.mock_pcan.WriteFD = Mock(return_value=PCAN_ERROR_OK)
        self.bus = can.Bus(bustype="pcan", fd=True)
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

            self.bus = can.Bus(bustype="pcan")
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
        self.bus = can.Bus(bustype="pcan")
        msg = can.Message(
            arbitration_id=0xC0FFEF, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=True
        )

        with self.assertRaises(PcanError):
            self.bus.send(msg)

    @parameterized.expand([("on", True), ("off", False)])
    def test_flash(self, name, flash) -> None:
        with self.subTest(name):
            self.bus = can.Bus(bustype="pcan")
            self.bus.flash(flash)
            call_list = self.mock_pcan.SetValue.call_args_list
            last_call_args_list = call_list[-1][0]
            self.assertEqual(
                last_call_args_list, (PCAN_USBBUS1, PCAN_CHANNEL_IDENTIFYING, flash)
            )

    def test_shutdown(self) -> None:
        self.bus = can.Bus(bustype="pcan")
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
            self.bus = can.Bus(bustype="pcan")

            self.bus.state = bus_state
            call_list = self.mock_pcan.SetValue.call_args_list
            last_call_args_list = call_list[-1][0]
            self.assertEqual(
                last_call_args_list,
                (PCAN_USBBUS1, PCAN_LISTEN_ONLY, expected_parameter),
            )

    def test_detect_available_configs(self) -> None:
        self.mock_pcan.GetValue = Mock(
            return_value=(PCAN_ERROR_OK, PCAN_CHANNEL_AVAILABLE)
        )
        configs = PcanBus._detect_available_configs()
        self.assertEqual(len(configs), 50)

    @parameterized.expand([("valid", PCAN_ERROR_OK, "OK"), ("invalid", 0x00005, None)])
    def test_status_string(self, name, status, expected_result) -> None:
        with self.subTest(name):
            self.bus = can.Bus(bustype="pcan")
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
            self.assertRaises(ValueError, can.Bus, bustype="pcan", device_id=dev_id)
        else:
            self.bus = can.Bus(bustype="pcan", device_id=dev_id)
            self.assertEqual(expected_result, self.bus.channel_info)

    def test_bus_creation_auto_reset(self):
        self.bus = can.Bus(bustype="pcan", auto_reset=True)
        self.assertIsInstance(self.bus, PcanBus)
        self.MockPCANBasic.assert_called_once()

    def test_auto_reset_init_fault(self):
        self.mock_pcan.SetValue = Mock(return_value=PCAN_ERROR_INITIALIZE)
        with self.assertRaises(CanInitializationError):
            self.bus = can.Bus(bustype="pcan", auto_reset=True)


if __name__ == "__main__":
    unittest.main()

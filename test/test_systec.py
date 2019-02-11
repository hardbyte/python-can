#!/usr/bin/env python
# coding: utf-8

import unittest
try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import can
from can.interfaces.systec import ucan, ucanbus
from can.interfaces.systec.ucan import *


class SystecTest(unittest.TestCase):

    def compare_message(self, first, second, msg):
        if first.arbitration_id != second.arbitration_id or first.data != second.data or \
                first.is_extended_id != second.is_extended_id:
            raise self.failureException(msg)

    def setUp(self):
        # add equality function for can.Message
        self.addTypeEqualityFunc(can.Message, self.compare_message)

        ucan.UcanInitHwConnectControlEx = Mock()
        ucan.UcanInitHardwareEx = Mock()
        ucan.UcanInitHardwareEx2 = Mock()
        ucan.UcanInitCanEx2 = Mock()
        ucan.UcanGetHardwareInfoEx2 = Mock()
        ucan.UcanSetAcceptanceEx = Mock()
        ucan.UcanDeinitCanEx = Mock()
        ucan.UcanDeinitHardware = Mock()
        ucan.UcanWriteCanMsgEx = Mock()
        ucan.UcanResetCanEx = Mock()
        self.bus = can.Bus(bustype='systec', channel=0, bitrate=125000)

    def test_bus_creation(self):
        self.assertIsInstance(self.bus, ucanbus.UcanBus)
        self.assertTrue(ucan.UcanInitHwConnectControlEx.called)
        self.assertTrue(ucan.UcanInitHardwareEx.called or ucan.UcanInitHardwareEx2.called)
        self.assertTrue(ucan.UcanInitCanEx2.called)
        self.assertTrue(ucan.UcanGetHardwareInfoEx2.called)
        self.assertTrue(ucan.UcanSetAcceptanceEx.called)

    def test_bus_shutdown(self):
        self.bus.shutdown()
        self.assertTrue(ucan.UcanDeinitCanEx.called)
        self.assertTrue(ucan.UcanDeinitHardware.called)

    def test_filter_setup(self):
        # no filter in the constructor
        expected_args = (
            (self.bus._ucan._handle, 0, AMR_ALL, ACR_ALL),
        )
        self.assertEqual(ucan.UcanSetAcceptanceEx.call_args, expected_args)

        # one filter is handled by the driver
        ucan.UcanSetAcceptanceEx.reset_mock()
        can_filter = (True, 0x123, 0x123, False, False)
        self.bus.set_filters(ucanbus.UcanBus.create_filter(*can_filter))
        expected_args = (
            (self.bus._ucan._handle,
             0,
             ucan.UcanServer.calculate_amr(*can_filter),
             ucan.UcanServer.calculate_acr(*can_filter)
             ),
        )
        self.assertEqual(ucan.UcanSetAcceptanceEx.call_args, expected_args)

        # multiple filters are handled by the bus
        ucan.UcanSetAcceptanceEx.reset_mock()
        can_filter = (
            (False, 0x8, 0x8, False, False),
            (False, 0x9, 0x9, False, False)
        )
        self.bus.set_filters(ucanbus.UcanBus.create_filter(*can_filter[0]) +
                             ucanbus.UcanBus.create_filter(*can_filter[1]))
        expected_args = (
            (self.bus._ucan._handle, 0, AMR_ALL, ACR_ALL),
        )
        self.assertEqual(ucan.UcanSetAcceptanceEx.call_args, expected_args)

    @patch('can.interfaces.systec.ucan.UcanServer.write_can_msg')
    def test_send_extended(self, mock_write_can_msg):
        msg = can.Message(
            arbitration_id=0xc0ffee,
            data=[0, 25, 0, 1, 3, 1, 4],
            is_extended_id=True)
        self.bus.send(msg)

        expected_args = (
            (0, [CanMsg(msg.arbitration_id, MsgFrameFormat.MSG_FF_EXT, msg.data)]),
        )
        self.assertEqual(mock_write_can_msg.call_args, expected_args)

    @patch('can.interfaces.systec.ucan.UcanServer.write_can_msg')
    def test_send_standard(self, mock_write_can_msg):
        msg = can.Message(
            arbitration_id=0x321,
            data=[50, 51],
            is_extended_id=False)
        self.bus.send(msg)

        expected_args = (
            (0, [CanMsg(msg.arbitration_id, MsgFrameFormat.MSG_FF_STD, msg.data)]),
        )
        self.assertEqual(mock_write_can_msg.call_args, expected_args)

    @patch('can.interfaces.systec.ucan.UcanServer.get_msg_pending')
    def test_recv_no_message(self, mock_get_msg_pending):
        mock_get_msg_pending.return_value = 0
        self.assertEqual(self.bus.recv(timeout=0.5), None)

    @patch('can.interfaces.systec.ucan.UcanServer.get_msg_pending')
    @patch('can.interfaces.systec.ucan.UcanServer.read_can_msg')
    def test_recv_extended(self, mock_read_can_msg, mock_get_msg_pending):
        mock_read_can_msg.return_value = [CanMsg(0xc0ffef, MsgFrameFormat.MSG_FF_EXT, [1, 2, 3, 4, 5, 6, 7, 8])], 0
        mock_get_msg_pending.return_value = 1

        msg = can.Message(
            arbitration_id=0xc0ffef,
            data=[1, 2, 3, 4, 5, 6, 7, 8],
            is_extended_id=True)
        can_msg = self.bus.recv()
        self.assertEqual(can_msg, msg)

    @patch('can.interfaces.systec.ucan.UcanServer.get_msg_pending')
    @patch('can.interfaces.systec.ucan.UcanServer.read_can_msg')
    def test_recv_standard(self, mock_read_can_msg, mock_get_msg_pending):
        mock_read_can_msg.return_value = [CanMsg(0x321, MsgFrameFormat.MSG_FF_STD, [50, 51])], 0
        mock_get_msg_pending.return_value = 1

        msg = can.Message(
            arbitration_id=0x321,
            data=[50, 51],
            is_extended_id=False)
        can_msg = self.bus.recv()
        self.assertEqual(can_msg, msg)

    @staticmethod
    def test_bus_defaults():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_NORMAL,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    @staticmethod
    def test_bus_channel():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=1)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            1,
            InitCanParam(
                Mode.MODE_NORMAL,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    @staticmethod
    def test_bus_bitrate():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0, bitrate=125000)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_NORMAL,
                Baudrate.BAUD_125kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    def test_bus_custom_bitrate(self):
        with self.assertRaises(ValueError):
            can.Bus(bustype='systec', channel=0, bitrate=123456)

    @staticmethod
    def test_receive_own_messages():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0, receive_own_messages=True)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_TX_ECHO,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    @staticmethod
    def test_bus_passive_state():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0, state=can.BusState.PASSIVE)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_LISTEN_ONLY,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    @staticmethod
    def test_rx_buffer_entries():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0, rx_buffer_entries=1024)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_NORMAL,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                1024,
                DEFAULT_BUFFER_ENTRIES
            )
        )

    @staticmethod
    def test_tx_buffer_entries():
        ucan.UcanInitCanEx2.reset_mock()
        bus = can.Bus(bustype='systec', channel=0, tx_buffer_entries=1024)
        ucan.UcanInitCanEx2.assert_called_once_with(
            bus._ucan._handle,
            0,
            InitCanParam(
                Mode.MODE_NORMAL,
                Baudrate.BAUD_500kBit,
                OutputControl.OCR_DEFAULT,
                AMR_ALL,
                ACR_ALL,
                BaudrateEx.BAUDEX_USE_BTR01,
                DEFAULT_BUFFER_ENTRIES,
                1024
            )
        )

    def test_flush_tx_buffer(self):
        self.bus.flush_tx_buffer()
        ucan.UcanResetCanEx.assert_called_once_with(self.bus._ucan._handle, 0, ResetFlags.RESET_ONLY_TX_BUFF)


if __name__ == '__main__':
    unittest.main()

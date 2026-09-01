#!/usr/bin/env python

""" """

import pickle
import unittest
from collections import deque
from contextlib import ExitStack
from threading import Event
from types import SimpleNamespace
from unittest.mock import patch

from can.interfaces.ics_neovi import ICSApiError
from can.interfaces.ics_neovi.neovi_bus import NeoViBus
from can.interfaces.ics_neovi import neovi_bus


class ICSApiErrorTest(unittest.TestCase):
    def test_error_pickling(self):
        iae = ICSApiError(
            0xF00,
            "description_short",
            "description_long",
            severity=ICSApiError.ICS_SPY_ERR_CRITICAL,
            restart_needed=1,
        )
        pickled_iae = pickle.dumps(iae)
        un_pickled_iae = pickle.loads(pickled_iae)
        assert iae.__dict__ == un_pickled_iae.__dict__


class NeoViBusBehaviorTest(unittest.TestCase):
    def test_channel_to_netid_accepts_integer_and_named_channel(self):
        fake_ics = SimpleNamespace(NETID_HSCAN=42)

        with ExitStack() as stack:
            stack.enter_context(patch.object(neovi_bus, "ics", fake_ics))
            stack.enter_context(
                patch.object(neovi_bus, "ICS_NETID_LOOKUP", {"HSCAN": 42}, create=True)
            )

            self.assertEqual(NeoViBus.channel_to_netid(7), 7)
            self.assertEqual(NeoViBus.channel_to_netid("8"), 8)
            self.assertEqual(NeoViBus.channel_to_netid("hscan"), 42)

    def test_channel_to_netid_rejects_unknown_channel_name(self):
        fake_ics = SimpleNamespace(NETID_HSCAN=42)

        with ExitStack() as stack:
            stack.enter_context(patch.object(neovi_bus, "ics", fake_ics))
            stack.enter_context(
                patch.object(neovi_bus, "ICS_NETID_LOOKUP", {"HSCAN": 42}, create=True)
            )

            with self.assertRaises(ValueError):
                NeoViBus.channel_to_netid("unknown")

    def test_ics_msg_to_message_converts_classic_frame(self):
        fake_ics = SimpleNamespace(
            SPY_PROTOCOL_CANFD=99,
            SPY_STATUS_XTD_FRAME=0x01,
            SPY_STATUS_REMOTE_FRAME=0x02,
            SPY_STATUS_TX_MSG=0x04,
            SPY_STATUS2_ERROR_FRAME=0x08,
            SPY_STATUS3_CANFD_ESI=0x10,
            SPY_STATUS3_CANFD_BRS=0x20,
        )
        bus = NeoViBus.__new__(NeoViBus)
        bus._use_system_timestamp = True
        bus._is_shutdown = True

        ics_msg = SimpleNamespace(
            Protocol=0,
            StatusBitField=fake_ics.SPY_STATUS_XTD_FRAME,
            StatusBitField2=0,
            StatusBitField3=0,
            NumberBytesData=4,
            NetworkID=0x34,
            NetworkID2=0x12,
            ArbIDOrHeader=0x123,
            ExtraDataPtrEnabled=0,
            ExtraDataPtr=tuple(),
            Data=(1, 2, 3, 4, 9, 9, 9, 9),
            TimeSystem=12.5,
        )

        with patch.object(neovi_bus, "ics", fake_ics):
            msg = bus._ics_msg_to_message(ics_msg)

        self.assertEqual(msg.timestamp, 12.5)
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertTrue(msg.is_extended_id)
        self.assertFalse(msg.is_remote_frame)
        self.assertFalse(msg.is_error_frame)
        self.assertFalse(msg.is_fd)
        self.assertTrue(msg.is_rx)
        self.assertEqual(msg.channel, 0x1234)
        self.assertEqual(msg.dlc, 4)
        self.assertEqual(bytes(msg.data), b"\x01\x02\x03\x04")

    def test_ics_msg_to_message_converts_fd_frame(self):
        fake_ics = SimpleNamespace(
            SPY_PROTOCOL_CANFD=99,
            SPY_STATUS_XTD_FRAME=0x01,
            SPY_STATUS_REMOTE_FRAME=0x02,
            SPY_STATUS_TX_MSG=0x04,
            SPY_STATUS2_ERROR_FRAME=0x08,
            SPY_STATUS3_CANFD_ESI=0x10,
            SPY_STATUS3_CANFD_BRS=0x20,
        )
        bus = NeoViBus.__new__(NeoViBus)
        bus._use_system_timestamp = True
        bus._is_shutdown = True

        ics_msg = SimpleNamespace(
            Protocol=fake_ics.SPY_PROTOCOL_CANFD,
            StatusBitField=0,
            StatusBitField2=fake_ics.SPY_STATUS2_ERROR_FRAME,
            StatusBitField3=fake_ics.SPY_STATUS3_CANFD_BRS
            | fake_ics.SPY_STATUS3_CANFD_ESI,
            NumberBytesData=12,
            NetworkID=5,
            NetworkID2=0,
            ArbIDOrHeader=0x456,
            ExtraDataPtrEnabled=1,
            ExtraDataPtr=tuple(range(16)),
            Data=tuple(range(8)),
            TimeSystem=3.25,
        )

        with patch.object(neovi_bus, "ics", fake_ics):
            msg = bus._ics_msg_to_message(ics_msg)

        self.assertEqual(msg.timestamp, 3.25)
        self.assertEqual(msg.arbitration_id, 0x456)
        self.assertFalse(msg.is_extended_id)
        self.assertFalse(msg.is_remote_frame)
        self.assertTrue(msg.is_error_frame)
        self.assertTrue(msg.is_fd)
        self.assertTrue(msg.is_rx)
        self.assertTrue(msg.bitrate_switch)
        self.assertTrue(msg.error_state_indicator)
        self.assertEqual(msg.channel, 5)
        self.assertEqual(msg.dlc, 12)
        self.assertEqual(bytes(msg.data), bytes(range(12)))

    def test_recv_internal_returns_none_when_no_message_available(self):
        bus = NeoViBus.__new__(NeoViBus)
        bus._is_shutdown = True
        bus.rx_buffer = deque()
        bus._process_msg_queue = lambda timeout=0.1: None

        msg, already_filtered = bus._recv_internal(timeout=0)

        self.assertIsNone(msg)
        self.assertFalse(already_filtered)

    def test_process_msg_queue_sets_receipt_without_echoing_transmit(self):
        fake_ics = SimpleNamespace(
            SPY_STATUS_TX_MSG=0x01,
            SPY_STATUS_GLOBAL_ERR=0x02,
            get_messages=lambda dev, include_errors, timeout: ((tx_msg,), 0),
        )
        tx_msg = SimpleNamespace(
            NetworkID=1,
            NetworkID2=0,
            StatusBitField=fake_ics.SPY_STATUS_TX_MSG,
            ArbIDOrHeader=0x321,
            DescriptionID=17,
        )
        receipt_key = (tx_msg.ArbIDOrHeader, tx_msg.DescriptionID)
        receipt_event = Event()
        bus = NeoViBus.__new__(NeoViBus)
        bus._is_shutdown = False
        bus.dev = object()
        bus.channels = [1]
        bus._channel_set = {1}
        bus.rx_buffer = deque()
        bus.message_receipts = {receipt_key: receipt_event}
        bus._receive_own_messages = False

        with patch.object(neovi_bus, "ics", fake_ics):
            bus._process_msg_queue(timeout=0)

        self.assertTrue(receipt_event.is_set())
        self.assertEqual(len(bus.rx_buffer), 0)
        bus._is_shutdown = True


if __name__ == "__main__":
    unittest.main()

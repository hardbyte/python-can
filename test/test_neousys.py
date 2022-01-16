#!/usr/bin/env python

import ctypes
import os
import pickle
import unittest
from unittest.mock import Mock

from ctypes import (
    byref,
    cast,
    POINTER,
    sizeof,
    c_ubyte,
)

import pytest

import can
from can.interfaces.neousys import neousys


class TestNeousysBus(unittest.TestCase):
    def setUp(self) -> None:
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB = Mock()
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_RegisterReceived = Mock(
            return_value=1
        )
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_RegisterStatus = Mock(
            return_value=1
        )
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Setup = Mock(return_value=1)
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Start = Mock(return_value=1)
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Send = Mock(return_value=1)
        can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Stop = Mock(return_value=1)
        self.bus = can.Bus(channel=0, bustype="neousys")

    def tearDown(self) -> None:
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def test_bus_creation(self) -> None:
        self.assertIsInstance(self.bus, neousys.NeousysBus)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Setup.called)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Start.called)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_RegisterReceived.called)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_RegisterStatus.called)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Send.not_called)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Stop.not_called)

        CAN_Start_args = (
            can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Setup.call_args[0]
        )

        # sizeof struct should be 16
        self.assertEqual(CAN_Start_args[0], 0)
        self.assertEqual(CAN_Start_args[2], 16)
        NeousysCanSetup_struct = cast(
            CAN_Start_args[1], POINTER(neousys.NeousysCanSetup)
        )
        self.assertEqual(NeousysCanSetup_struct.contents.bitRate, 500000)
        self.assertEqual(
            NeousysCanSetup_struct.contents.recvConfig,
            neousys.NEOUSYS_CAN_MSG_USE_ID_FILTER,
        )

    def test_bus_creation_bitrate(self) -> None:
        self.bus = can.Bus(channel=0, bustype="neousys", bitrate=200000)
        self.assertIsInstance(self.bus, neousys.NeousysBus)
        CAN_Start_args = (
            can.interfaces.neousys.neousys.NEOUSYS_CANLIB.CAN_Setup.call_args[0]
        )

        # sizeof struct should be 16
        self.assertEqual(CAN_Start_args[0], 0)
        self.assertEqual(CAN_Start_args[2], 16)
        NeousysCanSetup_struct = cast(
            CAN_Start_args[1], POINTER(neousys.NeousysCanSetup)
        )
        self.assertEqual(NeousysCanSetup_struct.contents.bitRate, 200000)
        self.assertEqual(
            NeousysCanSetup_struct.contents.recvConfig,
            neousys.NEOUSYS_CAN_MSG_USE_ID_FILTER,
        )

    def test_receive(self) -> None:
        recv_msg = self.bus.recv(timeout=0.05)
        self.assertEqual(recv_msg, None)
        msg_data = [0x01, 0x02, 0x03, 0x04, 0x05]
        NeousysCanMsg_msg = neousys.NeousysCanMsg(
            0x01, 0x00, 0x00, 0x05, (c_ubyte * 8)(*msg_data)
        )
        self.bus._neousys_recv_cb(byref(NeousysCanMsg_msg), sizeof(NeousysCanMsg_msg))
        recv_msg = self.bus.recv(timeout=0.05)
        self.assertEqual(recv_msg.dlc, 5)
        self.assertSequenceEqual(recv_msg.data, msg_data)

    def test_send(self) -> None:
        msg = can.Message(
            arbitration_id=0x01, data=[1, 2, 3, 4, 5, 6, 7, 8], is_extended_id=False
        )
        self.bus.send(msg)
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Send.called)

    def test_shutdown(self) -> None:
        self.bus.shutdown()
        self.assertTrue(neousys.NEOUSYS_CANLIB.CAN_Stop.called)


if __name__ == "__main__":
    unittest.main()

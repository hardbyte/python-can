#!/usr/bin/env python
# coding: utf-8

"""
Test for USB2Can_LibUSB
"""

import unittest
from unittest.mock import Mock

import pytest

import can
from can import Message
from can.interfaces.usb2can_libusb.usb2can_libusb_bus import (
    message_convert_rx,
    message_convert_tx,
    Usb2CanLibUsbBus,
)
from can.interfaces.usb2can_libusb.can_8dev_usb_utils import (
    Can8DevRxFrame,
    Can8DevCommandFrame,
    Can8DevCommand,
    can_8dev_open_frame,
)


class TestUsb2CanLibUsbBus(unittest.TestCase):
    def test_receive_deserialize(self) -> None:
        recv_packet = bytes.fromhex("55000000000121084ef1ff1f00007e00008355e0aa")
        recv_rx_frame = Can8DevRxFrame(recv_packet)
        recv_msg = message_convert_rx(recv_rx_frame)
        self.assertEqual(recv_msg.arbitration_id, 0x121)
        self.assertEqual(recv_msg.dlc, 8)
        self.assertEqual(
            recv_msg.data, bytes([0x4E, 0xF1, 0xFF, 0x1F, 0x00, 0x00, 0x7E, 0x00])
        )
        self.assertEqual(recv_msg.timestamp, 8607.200000)

    def test_transmit_serialize(self) -> None:
        send_packet = Message(
            arbitration_id=0xC0FFEE,
            is_extended_id=True,
            data=[0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
        )
        tx_frame = message_convert_tx(send_packet)
        tx_bytes = tx_frame.to_bytes()
        self.assertEqual(tx_bytes.hex(), "550100c0ffee080102030405060700aa")

    def test_command_serialize(self) -> None:
        frame = Can8DevCommandFrame(Can8DevCommand.USB_8DEV_RESET)
        self.assertEqual(frame.to_bytes().hex(), "11000100000000000000000000000022")
        deserialized_frame = Can8DevCommandFrame.from_bytes(frame.to_bytes())
        self.assertEqual(deserialized_frame.command, Can8DevCommand.USB_8DEV_RESET)

    def test_open_command(self) -> None:
        phase_seg1 = 6
        phase_seg2 = 1
        sjw = 1
        brp = 8
        loopback = True
        listenonly = False
        oneshot = False
        open_command = can_8dev_open_frame(
            phase_seg1, phase_seg2, sjw, brp, loopback, listenonly, oneshot
        )
        self.assertEqual(
            open_command.to_bytes().hex(), "11000209000601010008000000020022"
        )


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python

"""
"""

import unittest
from ctypes import c_ubyte
from unittest.mock import call, patch

import canalystii as driver  # low-level driver module, mock out this layer

import can
from can.interfaces.canalystii import CANalystIIBus


def create_mock_device():
    return patch("canalystii.CanalystDevice")


class CanalystIITest(unittest.TestCase):
    def test_initialize_from_constructor(self):
        with create_mock_device() as mock_device:
            instance = mock_device.return_value
            bus = CANalystIIBus(bitrate=1000000)

            self.assertEqual(bus.protocol, can.CanProtocol.CAN_20)

            instance.init.assert_has_calls(
                [
                    call(0, bitrate=1000000),
                    call(1, bitrate=1000000),
                ]
            )

    def test_initialize_single_channel_only(self):
        for channel in 0, 1:
            with create_mock_device() as mock_device:
                instance = mock_device.return_value
                bus = CANalystIIBus(channel, bitrate=1000000)

                self.assertEqual(bus.protocol, can.CanProtocol.CAN_20)
                instance.init.assert_called_once_with(channel, bitrate=1000000)

    def test_initialize_with_timing_registers(self):
        with create_mock_device() as mock_device:
            instance = mock_device.return_value
            timing = can.BitTiming.from_registers(
                f_clock=8_000_000, btr0=0x03, btr1=0x6F
            )
            bus = CANalystIIBus(bitrate=None, timing=timing)
            self.assertEqual(bus.protocol, can.CanProtocol.CAN_20)

            instance.init.assert_has_calls(
                [
                    call(0, timing0=0x03, timing1=0x6F),
                    call(1, timing0=0x03, timing1=0x6F),
                ]
            )

    def test_missing_bitrate(self):
        with self.assertRaises(ValueError) as cm:
            bus = CANalystIIBus(0, bitrate=None, timing=None)
        self.assertIn("bitrate", str(cm.exception))

    def test_receive_message(self):
        driver_message = driver.Message(
            can_id=0x333,
            timestamp=1000000,
            time_flag=1,
            send_type=0,
            remote=False,
            extended=False,
            data_len=8,
            data=(c_ubyte * 8)(*range(8)),
        )

        with create_mock_device() as mock_device:
            instance = mock_device.return_value
            instance.receive.return_value = [driver_message]
            bus = CANalystIIBus(bitrate=1000000)
            msg = bus.recv(0)
            self.assertEqual(driver_message.can_id, msg.arbitration_id)
            self.assertEqual(bytearray(driver_message.data), msg.data)

    def test_send_message(self):
        message = can.Message(arbitration_id=0x123, data=[3] * 8, is_extended_id=False)

        with create_mock_device() as mock_device:
            instance = mock_device.return_value
            bus = CANalystIIBus(channel=0, bitrate=5000000)
            bus.send(message)
            instance.send.assert_called_once()

            (channel, driver_messages, _timeout), _kwargs = instance.send.call_args
            self.assertEqual(0, channel)

            self.assertEqual(1, len(driver_messages))

            driver_message = driver_messages[0]
            self.assertEqual(message.arbitration_id, driver_message.can_id)
            self.assertEqual(message.data, bytearray(driver_message.data))
            self.assertEqual(8, driver_message.data_len)


if __name__ == "__main__":
    unittest.main()

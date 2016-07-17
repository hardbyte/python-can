#!/usr/bin/env python3
import ctypes
import unittest
import time
import logging
logging.basicConfig(level=logging.DEBUG)
import can
from can.interfaces.kvaser import canlib
from can.interfaces.kvaser import constants

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import patch, Mock


class KvaserTest(unittest.TestCase):
    
    def setUp(self):
        canlib.canGetNumberOfChannels = Mock(return_value=1)
        canlib.canOpenChannel = Mock(return_value=0)
        canlib.canIoCtl = Mock(return_value=0)
        canlib.canSetBusParams = Mock()
        canlib.canBusOn = Mock()
        canlib.canBusOff = Mock()
        canlib.canClose = Mock()
        canlib.canSetBusOutputControl = Mock()
        canlib.canGetChannelData = Mock()
        canlib.canWriteWait = self.canWriteWait
        canlib.canReadWait = self.canReadWait

        self.msg = {}
        self.msg_in_cue = None
        self.bus = can.interface.Bus(channel=0, bustype='kvaser')

    def tearDown(self):
        self.bus.shutdown()
        self.bus = None

    def test_bus_creation(self):
        self.assertIsInstance(self.bus, canlib.KvaserBus)
        self.assertTrue(canlib.canGetNumberOfChannels.called)
        self.assertTrue(canlib.canOpenChannel.called)
        self.assertTrue(canlib.canBusOn.called)

    def test_send_extended(self):
        msg = can.Message(
            arbitration_id=0xc0ffee,
            data=[0, 25, 0, 1, 3, 1, 4],
            extended_id=True)

        self.bus.send(msg)

        self.assertEqual(self.msg['arb_id'], 0xc0ffee)
        self.assertEqual(self.msg['dlc'], 7)
        self.assertEqual(self.msg['flags'], constants.canMSG_EXT)
        self.assertSequenceEqual(self.msg['data'], [0, 25, 0, 1, 3, 1, 4])

    def test_send_standard(self):
        msg = can.Message(
            arbitration_id=0x321,
            data=[50, 51],
            extended_id=False)

        self.bus.send(msg)

        self.assertEqual(self.msg['arb_id'], 0x321)
        self.assertEqual(self.msg['dlc'], 2)
        self.assertEqual(self.msg['flags'], 0)
        self.assertSequenceEqual(self.msg['data'], [50, 51])

    def test_recv_no_message(self):
        self.assertEqual(self.bus.recv(), None)

    def test_recv_extended(self):
        self.msg_in_cue = can.Message(
            arbitration_id=0xc0ffef,
            data=[1, 2, 3, 4, 5, 6, 7, 8],
            extended_id=True)

        now = time.time()
        msg = self.bus.recv()
        self.assertEqual(msg.arbitration_id, 0xc0ffef)
        self.assertEqual(msg.dlc, 8)
        self.assertEqual(msg.id_type, True)
        self.assertEqual(msg.data, self.msg_in_cue.data)
        self.assertTrue(now - 1 < msg.timestamp < now + 1)

    def test_recv_standard(self):
        self.msg_in_cue = can.Message(
            arbitration_id=0x123,
            data=[100, 101],
            extended_id=False)

        msg = self.bus.recv()
        self.assertEqual(msg.arbitration_id, 0x123)
        self.assertEqual(msg.dlc, 2)
        self.assertEqual(msg.id_type, False)
        self.assertSequenceEqual(msg.data, [100, 101])

    def canWriteWait(self, handle, arb_id, buf, dlc, flags, timeout):
        self.msg['arb_id'] = arb_id
        self.msg['dlc'] = dlc
        self.msg['flags'] = flags
        self.msg['data'] = bytearray(buf._obj)

    def canReadWait(self, handle, arb_id, data, dlc, flags, timestamp, timeout):
        if not self.msg_in_cue:
            return constants.canERR_NOMSG

        arb_id._obj.value = self.msg_in_cue.arbitration_id
        dlc._obj.value = self.msg_in_cue.dlc
        data._obj.raw = self.msg_in_cue.data
        flags_temp = 0
        if self.msg_in_cue.id_type:
            flags_temp |= constants.canMSG_EXT
        if self.msg_in_cue.is_remote_frame:
            flags_temp |= constants.canMSG_RTR
        if self.msg_in_cue.is_error_frame:
            flags_temp |= constants.canMSG_ERROR_FRAME
        flags._obj.value = flags_temp
        timestamp._obj.value = 0

        return constants.canOK

if __name__ == '__main__':
    unittest.main()

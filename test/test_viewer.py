#!/usr/bin/python
# coding: utf-8
#
# Copyright (C) 2018 Kristian Sloth Lauszus. All rights reserved.
#
# Contact information
# -------------------
# Kristian Sloth Lauszus
# Web      :  http://www.lauszus.com
# e-mail   :  lauszus@gmail.com

from __future__ import absolute_import

import argparse
import can
import curses
import datetime
import math
import pytest
import random
import struct
import time
import unittest
import os

from typing import Dict, Tuple, Union

try:
    # noinspection PyCompatibility
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

from can.scripts.viewer import KEY_ESC, KEY_SPACE, CanViewer, canopen_function_codes, CANOPEN_NMT, CANOPEN_SYNC_EMCY, \
    CANOPEN_TIME, CANOPEN_TPDO1, CANOPEN_RPDO1, CANOPEN_TPDO2, CANOPEN_RPDO2, CANOPEN_TPDO3, CANOPEN_RPDO3, \
    CANOPEN_TPDO4, CANOPEN_RPDO4, CANOPEN_SDO_TX, CANOPEN_SDO_RX, CANOPEN_HEARTBEAT, CANOPEN_LSS_TX, CANOPEN_LSS_RX, \
    parse_args


# noinspection SpellCheckingInspection,PyUnusedLocal
class StdscrDummy:

    def __init__(self):
        self.key_counter = 0

    @staticmethod
    def clear():
        pass

    @staticmethod
    def erase():
        pass

    @staticmethod
    def getmaxyx():
        # Set y-value, so scrolling gets tested
        return 1, 1

    @staticmethod
    def addstr(row, col, txt, *args):
        assert row >= 0
        assert col >= 0
        assert txt is not None
        # Raise an exception 50 % of the time, so we can make sure the code handles it
        if random.random() < .5:
            raise curses.error

    @staticmethod
    def nodelay(_bool):
        pass

    def getch(self):
        self.key_counter += 1
        if self.key_counter == 1:
            # Send invalid key
            return -1
        elif self.key_counter == 2:
            return ord('c')
        elif self.key_counter == 3:
            return KEY_SPACE  # Pause
        elif self.key_counter == 4:
            return KEY_SPACE  # Unpause

        # Keep scrolling until it exceeds the number of messages
        elif self.key_counter <= 100:
            return curses.KEY_DOWN
        # Scroll until the header is back as the first line and then scroll over the limit
        elif self.key_counter <= 200:
            return curses.KEY_UP

        return KEY_ESC


class CanViewerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Set seed, so the tests are not affected
        random.seed(0)

    def setUp(self):
        stdscr = StdscrDummy()
        config = {'interface': 'virtual', 'receive_own_messages': True}
        bus = can.Bus(**config)
        data_structs = None
        ignore_canopen = False

        patch_curs_set = patch('curses.curs_set')
        patch_curs_set.start()
        self.addCleanup(patch_curs_set.stop)

        patch_use_default_colors = patch('curses.use_default_colors')
        patch_use_default_colors.start()
        self.addCleanup(patch_use_default_colors.stop)

        patch_is_term_resized = patch('curses.is_term_resized')
        mock_is_term_resized = patch_is_term_resized.start()
        mock_is_term_resized.return_value = True if random.random() < .5 else False
        self.addCleanup(patch_is_term_resized.stop)

        if hasattr(curses, 'resizeterm'):
            patch_resizeterm = patch('curses.resizeterm')
            patch_resizeterm.start()
            self.addCleanup(patch_resizeterm.stop)

        self.can_viewer = CanViewer(stdscr, bus, data_structs, ignore_canopen, testing=True)

    def tearDown(self):
        # Run the viewer after the test, this is done, so we can receive the CAN-Bus messages and make sure that they
        # are parsed correctly
        self.can_viewer.run()

    def test_canopen(self):
        # NMT
        data = [2, 1]  # cmd = stop node, node ID = 1
        msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('NMT', '0x01'))

        msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=True)  # CANopen do not use an extended id
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # The ID is not added to the NMT function code
        msg = can.Message(arbitration_id=CANOPEN_NMT + 1, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        data = [2, 128]  # cmd = stop node, node ID = invalid id
        msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        data = [1, 0]  # cmd = start node, node ID = all
        msg = can.Message(arbitration_id=CANOPEN_NMT, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('NMT', 'ALL'))

        # SYNC
        # The ID is not added to the SYNC function code
        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=None, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        data = [1, 2, 3, 4, 5, 6, 7, 8]  # Wrong length
        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY, data=None, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('SYNC', None))

        # EMCY
        data = [1, 2, 3, 4, 5, 6, 7]  # Wrong length
        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        tmp = self.can_viewer.parse_canopen_message(msg)
        self.assertTupleEqual(tmp, (None, None))

        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 128, data=data, extended_id=False)  # Invalid ID
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        msg = can.Message(arbitration_id=CANOPEN_SYNC_EMCY + 1, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('EMCY', '0x01'))

        # TIME
        one_day_seconds = 24 * 60 * 60
        offset = datetime.datetime(year=1984, month=1, day=1)
        now = datetime.datetime.now()
        delta = (now - offset).total_seconds()
        days, seconds = divmod(delta, one_day_seconds)
        time_struct = struct.Struct('<LH')
        data = time_struct.pack(round(seconds * 1000), int(days))
        msg = can.Message(arbitration_id=CANOPEN_TIME, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('TIME', None))

        # The ID is not added to the TIME function code
        msg = can.Message(arbitration_id=CANOPEN_TIME + 1, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # milliseconds, days = time_struct.unpack(data)
        # seconds = days * one_day_seconds + milliseconds / 1000.
        # now_unpacked = datetime.datetime.utcfromtimestamp(
        #     seconds + (offset - datetime.datetime.utcfromtimestamp(0)).total_seconds())

        # TPDO1, RPDO1, TPDO2, RPDO2, TPDO3, RPDO3, TPDO4, RPDO4
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        for i, func_code in enumerate([CANOPEN_TPDO1, CANOPEN_RPDO1, CANOPEN_TPDO2, CANOPEN_RPDO2,
                                       CANOPEN_TPDO3, CANOPEN_RPDO3, CANOPEN_TPDO4, CANOPEN_RPDO4]):
            node_id = i + 1
            msg = can.Message(arbitration_id=func_code + node_id, data=data, extended_id=False)
            self.can_viewer.bus.send(msg)
            self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (canopen_function_codes[func_code],
                                                                               '0x{0:02X}'.format(node_id)))

        # Set invalid node ID
        msg = can.Message(arbitration_id=CANOPEN_TPDO1 + 128, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # SDO_TX
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=CANOPEN_SDO_TX + 0x10, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('SDO_TX', '0x10'))

        data = [1, 2, 3, 4]  # Invalid data length
        msg = can.Message(arbitration_id=CANOPEN_SDO_TX + 0x10, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # SDO_RX
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=CANOPEN_SDO_RX + 0x20, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('SDO_RX', '0x20'))

        # HEARTBEAT
        data = [0x05]  # Operational
        msg = can.Message(arbitration_id=CANOPEN_HEARTBEAT + 0x7F, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('HEARTBEAT', '0x7F'))

        # LSS_TX
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=CANOPEN_LSS_TX, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('LSS_TX', None))

        # LSS_RX
        msg = can.Message(arbitration_id=CANOPEN_LSS_RX, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), ('LSS_RX', None))

        # Send ID that does not match any of the function codes
        msg = can.Message(arbitration_id=CANOPEN_LSS_RX + 1, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # Send non-CANopen message
        msg = can.Message(arbitration_id=0x101, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # Send the same command, but with another data length
        data = [1, 2, 3, 4, 5, 6]
        msg = can.Message(arbitration_id=0x101, data=data, extended_id=False)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # Message with extended id
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=0x123456, data=data, extended_id=True)
        self.can_viewer.bus.send(msg)
        self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # Send the same message again to make sure that resending works and dt is correct
        time.sleep(.1)
        self.can_viewer.bus.send(msg)

    def test_receive(self):
        # Send the messages again, but this time the test code will receive it
        self.test_canopen()

        data_structs = {
            # For converting the EMCY and HEARTBEAT messages
            0x080 + 0x01: struct.Struct('<HBLB'),
            0x700 + 0x7F: struct.Struct('<B'),

            # Big-endian and float test
            0x123456: struct.Struct('>ff'),
        }
        # Receive the messages we just sent in 'test_canopen'
        while 1:
            msg = self.can_viewer.bus.recv(timeout=0)
            if msg is not None:
                self.can_viewer.data_structs = data_structs if msg.arbitration_id != 0x101 else None
                self.can_viewer.ignore_canopen = False if msg.arbitration_id != 0x123456 else True
                _id = self.can_viewer.draw_can_bus_message(msg)
                if _id['msg'].arbitration_id == 0x101:
                    # Check if the counter is reset when the length has changed
                    self.assertEqual(_id['count'], 1)
                elif _id['msg'].arbitration_id == 0x123456:
                    # Check if the counter is incremented
                    if _id['dt'] == 0:
                        self.assertEqual(_id['count'], 1)
                    else:
                        self.assertTrue(pytest.approx(_id['dt'], 0.1))  # dt should be ~0.1 s
                        self.assertEqual(_id['count'], 2)
                else:
                    # Make sure dt is 0
                    if _id['count'] == 1:
                        self.assertEqual(_id['dt'], 0)
            else:
                break

    def test_pack_unpack(self):
        # Dictionary used to convert between Python values and C structs represented as Python strings.
        # If the value is 'None' then the message does not contain any data package.
        #
        # The struct package is used to unpack the received data.
        # Note the data is assumed to be in little-endian byte order.
        # < = little-endian, > = big-endian
        # x = pad byte
        # c = char
        # ? = bool
        # b = int8_t, B = uint8_t
        # h = int16, H = uint16
        # l = int32_t, L = uint32_t
        # q = int64_t, Q = uint64_t
        # f = float (32-bits), d = double (64-bits)
        #
        # An optional conversion from real units to integers can be given as additional arguments.
        # In order to convert from raw integer value the SI-units are multiplied with the values and similarly the values
        # are divided by the value in order to convert from real units to raw integer values.
        data_structs = {
            # CANopen node 1
            CANOPEN_TPDO1 + 1: struct.Struct('<bBh2H'),
            CANOPEN_TPDO2 + 1: (struct.Struct('<HHB'), 100., 10., 1),
            CANOPEN_TPDO3 + 1: struct.Struct('<ff'),
            CANOPEN_TPDO4 + 1: (struct.Struct('<ff'), math.pi / 180., math.pi / 180.),
            CANOPEN_TPDO1 + 2: None,
            CANOPEN_TPDO2 + 2: struct.Struct('>lL'),
            (CANOPEN_TPDO3 + 2, CANOPEN_TPDO4 + 2): struct.Struct('>LL'),
        }  # type: Dict[Union[int, Tuple[int, ...]], Union[struct.Struct, Tuple, None]]

        raw_data = CanViewer.pack_data(CANOPEN_TPDO1 + 1, data_structs, -7, 13, -1024, 2048, 0xFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO1 + 1, data_structs, raw_data)
        self.assertListEqual(parsed_data, [-7, 13, -1024, 2048, 0xFFFF])
        self.assertTrue(all(isinstance(d, int) for d in parsed_data))

        raw_data = CanViewer.pack_data(CANOPEN_TPDO2 + 1, data_structs, 12.34, 4.5, 6)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO2 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [12.34, 4.5, 6]))
        self.assertTrue(isinstance(parsed_data[0], float) and isinstance(parsed_data[1], float) and
                        isinstance(parsed_data[2], int))

        raw_data = CanViewer.pack_data(CANOPEN_TPDO3 + 1, data_structs, 123.45, 67.89)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO3 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [123.45, 67.89]))
        self.assertTrue(all(isinstance(d, float) for d in parsed_data))

        raw_data = CanViewer.pack_data(CANOPEN_TPDO4 + 1, data_structs, math.pi / 2., math.pi)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO4 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [math.pi / 2., math.pi]))
        self.assertTrue(all(isinstance(d, float) for d in parsed_data))

        raw_data = CanViewer.pack_data(CANOPEN_TPDO1 + 2, data_structs)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO1 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [])
        self.assertIsInstance(parsed_data, list)

        raw_data = CanViewer.pack_data(CANOPEN_TPDO2 + 2, data_structs, -2147483648, 0xFFFFFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO2 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [-2147483648, 0xFFFFFFFF])

        raw_data = CanViewer.pack_data(CANOPEN_TPDO3 + 2, data_structs, 0xFF, 0xFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO3 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [0xFF, 0xFFFF])

        raw_data = CanViewer.pack_data(CANOPEN_TPDO4 + 2, data_structs, 0xFFFFFF, 0xFFFFFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO4 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [0xFFFFFF, 0xFFFFFFFF])

        # See: http://python-future.org/compatible_idioms.html#long-integers
        from past.builtins import long
        self.assertTrue(all(isinstance(d, (int, long)) for d in parsed_data))

        # Make sure that the ValueError exception is raised
        with self.assertRaises(ValueError):
            CanViewer.pack_data(0x101, data_structs, 1, 2, 3, 4)

        with self.assertRaises(ValueError):
            CanViewer.unpack_data(0x102, data_structs, b'\x01\x02\x03\x04\x05\x06\x07\x08')

    def test_parse_args(self):
        parsed_args, _, _, _ = parse_args(['-b', '250000'])
        self.assertEqual(parsed_args.bitrate, 250000)

        parsed_args, _, _, _ = parse_args(['--bitrate', '500000'])
        self.assertEqual(parsed_args.bitrate, 500000)

        parsed_args, _, _, _ = parse_args(['-c', 'can0'])
        self.assertEqual(parsed_args.channel, 'can0')

        parsed_args, _, _, _ = parse_args(['--channel', 'PCAN_USBBUS1'])
        self.assertEqual(parsed_args.channel, 'PCAN_USBBUS1')

        parsed_args, _, _, ignore_canopen = parse_args([])
        self.assertFalse(parsed_args.ignore_canopen)
        self.assertFalse(ignore_canopen)

        parsed_args, _, _, ignore_canopen = parse_args(['--ignore-canopen'])
        self.assertTrue(parsed_args.ignore_canopen)
        self.assertTrue(ignore_canopen)

        parsed_args, _, data_structs, _ = parse_args(['-d', '100:<L'])
        self.assertEqual(parsed_args.decode, ['100:<L'])

        self.assertIsInstance(data_structs, dict)
        self.assertEqual(len(data_structs), 1)

        self.assertIsInstance(data_structs[0x100], struct.Struct)
        self.assertIn(data_structs[0x100].format, ['<L', b'<L'])
        self.assertEqual(data_structs[0x100].size, 4)

        f = open('test.txt', 'w')
        f.write('100:<BB\n101:<HH\n')
        f.close()
        parsed_args, _, data_structs, _ = parse_args(['-d', 'test.txt'])

        self.assertIsInstance(data_structs, dict)
        self.assertEqual(len(data_structs), 2)

        self.assertIsInstance(data_structs[0x100], struct.Struct)
        self.assertIn(data_structs[0x100].format, ['<BB', b'<BB'])
        self.assertEqual(data_structs[0x100].size, 2)

        self.assertIsInstance(data_structs[0x101], struct.Struct)
        self.assertIn(data_structs[0x101].format, ['<HH', b'<HH'])
        self.assertEqual(data_structs[0x101].size, 4)
        os.remove('test.txt')

        parsed_args, _, data_structs, _ = parse_args(['--decode', '100:<LH:10.:100.', '101:<ff', '102:<Bf:1:57.3'])
        self.assertEqual(parsed_args.decode, ['100:<LH:10.:100.', '101:<ff', '102:<Bf:1:57.3'])

        self.assertIsInstance(data_structs, dict)
        self.assertEqual(len(data_structs), 3)

        self.assertIsInstance(data_structs[0x100], tuple)
        self.assertEqual(len(data_structs[0x100]), 3)

        self.assertIsInstance(data_structs[0x100][0], struct.Struct)
        self.assertIsInstance(data_structs[0x100][1], float)
        self.assertIsInstance(data_structs[0x100][2], float)
        self.assertIn(data_structs[0x100][0].format, ['<LH', b'<LH'])
        self.assertEqual(data_structs[0x100][0].size, 6)
        self.assertEqual(data_structs[0x100][1], 10.0)
        self.assertEqual(data_structs[0x100][2], 100.0)

        self.assertIsInstance(data_structs[0x101], struct.Struct)
        self.assertIn(data_structs[0x101].format, ['<ff', b'<ff'])
        self.assertEqual(data_structs[0x101].size, 8)

        self.assertIsInstance(data_structs[0x102][0], struct.Struct)
        self.assertIsInstance(data_structs[0x102][1], int)
        self.assertIsInstance(data_structs[0x102][2], float)
        self.assertIn(data_structs[0x102][0].format, ['<Bf', b'<Bf'])
        self.assertEqual(data_structs[0x102][0].size, 5)
        self.assertEqual(data_structs[0x102][1], 1)
        self.assertAlmostEqual(data_structs[0x102][2], 57.3)

        parsed_args, can_filters, _, _ = parse_args(['-f', '100:7FF'])
        self.assertEqual(parsed_args.filter, ['100:7FF'])
        self.assertIsInstance(can_filters, list)
        self.assertIsInstance(can_filters[0], dict)
        self.assertEqual(can_filters[0]['can_id'], 0x100)
        self.assertEqual(can_filters[0]['can_mask'], 0x7FF)

        parsed_args, can_filters, _, _ = parse_args(['-f', '101:7FF', '102:7FC'])
        self.assertEqual(parsed_args.filter, ['101:7FF', '102:7FC'])
        self.assertIsInstance(can_filters, list)
        self.assertIsInstance(can_filters[0], dict)
        self.assertIsInstance(can_filters[1], dict)
        self.assertEqual(can_filters[0]['can_id'], 0x101)
        self.assertEqual(can_filters[0]['can_mask'], 0x7FF)
        self.assertEqual(can_filters[1]['can_id'], 0x102)
        self.assertEqual(can_filters[1]['can_mask'], 0x7FC)

        with self.assertRaises(argparse.ArgumentError):
            parse_args(['-f', '101,7FF'])

        parsed_args, can_filters, _, _ = parse_args(['--filter', '100~7FF'])
        self.assertEqual(parsed_args.filter, ['100~7FF'])
        self.assertIsInstance(can_filters, list)
        self.assertIsInstance(can_filters[0], dict)
        self.assertEqual(can_filters[0]['can_id'], 0x100 | 0x20000000)
        self.assertEqual(can_filters[0]['can_mask'], 0x7FF & 0x20000000)

        parsed_args, _, _, _ = parse_args(['-i', 'socketcan'])
        self.assertEqual(parsed_args.interface, 'socketcan')

        parsed_args, _, _, _ = parse_args(['--interface', 'pcan'])
        self.assertEqual(parsed_args.interface, 'pcan')


if __name__ == '__main__':
    unittest.main()

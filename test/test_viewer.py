#!/usr/bin/python
# coding: utf-8
#
# Copyright (C) 2018 Kristian Sloth Lauszus.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
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
import math
import pytest
import random
import struct
import time
import unittest
import os
import six

from typing import Dict, Tuple, Union

try:
    # noinspection PyCompatibility
    from unittest.mock import Mock, patch
except ImportError:
    # noinspection PyPackageRequirements
    from mock import Mock, patch

from can.viewer import KEY_ESC, KEY_SPACE, CanViewer, parse_args


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
            return ord('c')  # Clear
        elif self.key_counter == 3:
            return KEY_SPACE  # Pause
        elif self.key_counter == 4:
            return KEY_SPACE  # Unpause
        elif self.key_counter == 5:
            return ord('s')  # Sort

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

        patch_curs_set = patch('curses.curs_set')
        patch_curs_set.start()
        self.addCleanup(patch_curs_set.stop)

        patch_use_default_colors = patch('curses.use_default_colors')
        patch_use_default_colors.start()
        self.addCleanup(patch_use_default_colors.stop)

        patch_init_pair = patch('curses.init_pair')
        patch_init_pair.start()
        self.addCleanup(patch_init_pair.stop)

        patch_color_pair = patch('curses.color_pair')
        patch_color_pair.start()
        self.addCleanup(patch_color_pair.stop)

        patch_is_term_resized = patch('curses.is_term_resized')
        mock_is_term_resized = patch_is_term_resized.start()
        mock_is_term_resized.return_value = True if random.random() < .5 else False
        self.addCleanup(patch_is_term_resized.stop)

        if hasattr(curses, 'resizeterm'):
            patch_resizeterm = patch('curses.resizeterm')
            patch_resizeterm.start()
            self.addCleanup(patch_resizeterm.stop)

        self.can_viewer = CanViewer(stdscr, bus, data_structs, testing=True)

    def tearDown(self):
        # Run the viewer after the test, this is done, so we can receive the CAN-Bus messages and make sure that they
        # are parsed correctly
        self.can_viewer.run()

    def test_send(self):
        # CANopen EMCY
        data = [1, 2, 3, 4, 5, 6, 7]  # Wrong length
        msg = can.Message(arbitration_id=0x080 + 1, data=data, is_extended_id=False)
        self.can_viewer.bus.send(msg)

        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=0x080 + 1, data=data, is_extended_id=False)
        self.can_viewer.bus.send(msg)

        # CANopen HEARTBEAT
        data = [0x05]  # Operational
        msg = can.Message(arbitration_id=0x700 + 0x7F, data=data, is_extended_id=False)
        self.can_viewer.bus.send(msg)

        # Send non-CANopen message
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=0x101, data=data, is_extended_id=False)
        self.can_viewer.bus.send(msg)

        # Send the same command, but with another data length
        data = [1, 2, 3, 4, 5, 6]
        msg = can.Message(arbitration_id=0x101, data=data, is_extended_id=False)
        self.can_viewer.bus.send(msg)

        # Message with extended id
        data = [1, 2, 3, 4, 5, 6, 7, 8]
        msg = can.Message(arbitration_id=0x123456, data=data, is_extended_id=True)
        self.can_viewer.bus.send(msg)
        # self.assertTupleEqual(self.can_viewer.parse_canopen_message(msg), (None, None))

        # Send the same message again to make sure that resending works and dt is correct
        time.sleep(.1)
        self.can_viewer.bus.send(msg)

        # Send error message
        msg = can.Message(is_error_frame=True)
        self.can_viewer.bus.send(msg)

    def test_receive(self):
        # Send the messages again, but this time the test code will receive it
        self.test_send()

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

    # Convert it into raw integer values and then pack the data
    @staticmethod
    def pack_data(cmd, cmd_to_struct, *args):  # type: (int, Dict, Union[*float, *int]) -> bytes
        if not cmd_to_struct or len(args) == 0:
            # If no arguments are given, then the message does not contain a data package
            return b''

        for key in cmd_to_struct.keys():
            if cmd == key if isinstance(key, int) else cmd in key:
                value = cmd_to_struct[key]
                if isinstance(value, tuple):
                    # The struct is given as the fist argument
                    struct_t = value[0]  # type: struct.Struct

                    # The conversion from SI-units to raw values are given in the rest of the tuple
                    fmt = struct_t.format
                    if isinstance(fmt, six.string_types):  # pragma: no cover
                        # Needed for Python 3.7
                        fmt = six.b(fmt)

                    # Make sure the endian is given as the first argument
                    assert six.byte2int(fmt) == ord('<') or six.byte2int(fmt) == ord('>')

                    # Disable rounding if the format is a float
                    data = []
                    for c, arg, val in zip(six.iterbytes(fmt[1:]), args, value[1:]):
                        if c == ord('f'):
                            data.append(arg * val)
                        else:
                            data.append(round(arg * val))
                else:
                    # No conversion from SI-units is needed
                    struct_t = value  # type: struct.Struct
                    data = args

                return struct_t.pack(*data)
        else:
            raise ValueError('Unknown command: 0x{:02X}'.format(cmd))

    def test_pack_unpack(self):
        CANOPEN_TPDO1 = 0x180
        CANOPEN_TPDO2 = 0x280
        CANOPEN_TPDO3 = 0x380
        CANOPEN_TPDO4 = 0x480

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

        raw_data = self.pack_data(CANOPEN_TPDO1 + 1, data_structs, -7, 13, -1024, 2048, 0xFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO1 + 1, data_structs, raw_data)
        self.assertListEqual(parsed_data, [-7, 13, -1024, 2048, 0xFFFF])
        self.assertTrue(all(isinstance(d, int) for d in parsed_data))

        raw_data = self.pack_data(CANOPEN_TPDO2 + 1, data_structs, 12.34, 4.5, 6)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO2 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [12.34, 4.5, 6]))
        self.assertTrue(isinstance(parsed_data[0], float) and isinstance(parsed_data[1], float) and
                        isinstance(parsed_data[2], int))

        raw_data = self.pack_data(CANOPEN_TPDO3 + 1, data_structs, 123.45, 67.89)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO3 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [123.45, 67.89]))
        self.assertTrue(all(isinstance(d, float) for d in parsed_data))

        raw_data = self.pack_data(CANOPEN_TPDO4 + 1, data_structs, math.pi / 2., math.pi)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO4 + 1, data_structs, raw_data)
        self.assertTrue(pytest.approx(parsed_data, [math.pi / 2., math.pi]))
        self.assertTrue(all(isinstance(d, float) for d in parsed_data))

        raw_data = self.pack_data(CANOPEN_TPDO1 + 2, data_structs)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO1 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [])
        self.assertIsInstance(parsed_data, list)

        raw_data = self.pack_data(CANOPEN_TPDO2 + 2, data_structs, -2147483648, 0xFFFFFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO2 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [-2147483648, 0xFFFFFFFF])

        raw_data = self.pack_data(CANOPEN_TPDO3 + 2, data_structs, 0xFF, 0xFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO3 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [0xFF, 0xFFFF])

        raw_data = self.pack_data(CANOPEN_TPDO4 + 2, data_structs, 0xFFFFFF, 0xFFFFFFFF)
        parsed_data = CanViewer.unpack_data(CANOPEN_TPDO4 + 2, data_structs, raw_data)
        self.assertListEqual(parsed_data, [0xFFFFFF, 0xFFFFFFFF])

        # See: http://python-future.org/compatible_idioms.html#long-integers
        from past.builtins import long
        self.assertTrue(all(isinstance(d, (int, long)) for d in parsed_data))

        # Make sure that the ValueError exception is raised
        with self.assertRaises(ValueError):
            self.pack_data(0x101, data_structs, 1, 2, 3, 4)

        with self.assertRaises(ValueError):
            CanViewer.unpack_data(0x102, data_structs, b'\x01\x02\x03\x04\x05\x06\x07\x08')

    def test_parse_args(self):
        parsed_args, _, _ = parse_args(['-b', '250000'])
        self.assertEqual(parsed_args.bitrate, 250000)

        parsed_args, _, _ = parse_args(['--bitrate', '500000'])
        self.assertEqual(parsed_args.bitrate, 500000)

        parsed_args, _, _ = parse_args(['-c', 'can0'])
        self.assertEqual(parsed_args.channel, 'can0')

        parsed_args, _, _ = parse_args(['--channel', 'PCAN_USBBUS1'])
        self.assertEqual(parsed_args.channel, 'PCAN_USBBUS1')

        parsed_args, _, data_structs = parse_args(['-d', '100:<L'])
        self.assertEqual(parsed_args.decode, ['100:<L'])

        self.assertIsInstance(data_structs, dict)
        self.assertEqual(len(data_structs), 1)

        self.assertIsInstance(data_structs[0x100], struct.Struct)
        self.assertIn(data_structs[0x100].format, ['<L', b'<L'])
        self.assertEqual(data_structs[0x100].size, 4)

        f = open('test.txt', 'w')
        f.write('100:<BB\n101:<HH\n')
        f.close()
        parsed_args, _, data_structs = parse_args(['-d', 'test.txt'])

        self.assertIsInstance(data_structs, dict)
        self.assertEqual(len(data_structs), 2)

        self.assertIsInstance(data_structs[0x100], struct.Struct)
        self.assertIn(data_structs[0x100].format, ['<BB', b'<BB'])
        self.assertEqual(data_structs[0x100].size, 2)

        self.assertIsInstance(data_structs[0x101], struct.Struct)
        self.assertIn(data_structs[0x101].format, ['<HH', b'<HH'])
        self.assertEqual(data_structs[0x101].size, 4)
        os.remove('test.txt')

        parsed_args, _, data_structs = parse_args(['--decode', '100:<LH:10.:100.', '101:<ff', '102:<Bf:1:57.3'])
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

        parsed_args, can_filters, _ = parse_args(['-f', '100:7FF'])
        self.assertEqual(parsed_args.filter, ['100:7FF'])
        self.assertIsInstance(can_filters, list)
        self.assertIsInstance(can_filters[0], dict)
        self.assertEqual(can_filters[0]['can_id'], 0x100)
        self.assertEqual(can_filters[0]['can_mask'], 0x7FF)

        parsed_args, can_filters, _ = parse_args(['-f', '101:7FF', '102:7FC'])
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

        parsed_args, can_filters, _ = parse_args(['--filter', '100~7FF'])
        self.assertEqual(parsed_args.filter, ['100~7FF'])
        self.assertIsInstance(can_filters, list)
        self.assertIsInstance(can_filters[0], dict)
        self.assertEqual(can_filters[0]['can_id'], 0x100 | 0x20000000)
        self.assertEqual(can_filters[0]['can_mask'], 0x7FF & 0x20000000)

        parsed_args, _, _ = parse_args(['-i', 'socketcan'])
        self.assertEqual(parsed_args.interface, 'socketcan')

        parsed_args, _, _ = parse_args(['--interface', 'pcan'])
        self.assertEqual(parsed_args.interface, 'pcan')

        # Make sure it exits with the correct error code when displaying the help page
        # See: https://github.com/hardbyte/python-can/issues/427
        with self.assertRaises(SystemExit) as cm:
            parse_args(['-h'])
        self.assertEqual(cm.exception.code, 0)

        with self.assertRaises(SystemExit) as cm:
            parse_args([])
        import errno
        self.assertEqual(cm.exception.code, errno.EINVAL)


if __name__ == '__main__':
    unittest.main()

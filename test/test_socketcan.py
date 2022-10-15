#!/usr/bin/env python

"""
Test functions in `can.interfaces.socketcan.socketcan`.
"""
import ctypes
import struct
import unittest
from unittest.mock import patch

from can.interfaces.socketcan.socketcan import (
    bcm_header_factory,
    build_bcm_header,
    build_bcm_tx_delete_header,
    build_bcm_transmit_header,
    build_bcm_update_header,
    BcmMsgHead,
)
from can.interfaces.socketcan.constants import (
    CAN_BCM_TX_DELETE,
    CAN_BCM_TX_SETUP,
    SETTIMER,
    STARTTIMER,
    TX_COUNTEVT,
)


class SocketCANTest(unittest.TestCase):
    def setUp(self):
        self._ctypes_sizeof = ctypes.sizeof
        self._ctypes_alignment = ctypes.alignment

    @patch("ctypes.sizeof")
    @patch("ctypes.alignment")
    def test_bcm_header_factory_32_bit_sizeof_long_4_alignof_long_4(
        self, ctypes_sizeof, ctypes_alignment
    ):
        """This tests a 32-bit platform (ex. Debian Stretch on i386), where:

        * sizeof(long) == 4
        * sizeof(long long) == 8
        * alignof(long) == 4
        * alignof(long long) == 4
        """

        def side_effect_ctypes_sizeof(value):
            type_to_size = {
                ctypes.c_longlong: 8,
                ctypes.c_long: 4,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 8,
            }
            return type_to_size[value]

        def side_effect_ctypes_alignment(value):
            type_to_alignment = {
                ctypes.c_longlong: 4,
                ctypes.c_long: 4,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 4,
            }
            return type_to_alignment[value]

        ctypes_sizeof.side_effect = side_effect_ctypes_sizeof
        ctypes_alignment.side_effect = side_effect_ctypes_alignment

        fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
        ]
        BcmMsgHead = bcm_header_factory(fields)

        expected_fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
            # We expect 4 bytes of padding
            ("pad_0", ctypes.c_uint8),
            ("pad_1", ctypes.c_uint8),
            ("pad_2", ctypes.c_uint8),
            ("pad_3", ctypes.c_uint8),
        ]
        self.assertEqual(expected_fields, BcmMsgHead._fields_)

    @patch("ctypes.sizeof")
    @patch("ctypes.alignment")
    def test_bcm_header_factory_32_bit_sizeof_long_4_alignof_long_long_8(
        self, ctypes_sizeof, ctypes_alignment
    ):
        """This tests a 32-bit platform (ex. Raspbian Stretch on armv7l), where:

        * sizeof(long) == 4
        * sizeof(long long) == 8
        * alignof(long) == 4
        * alignof(long long) == 8
        """

        def side_effect_ctypes_sizeof(value):
            type_to_size = {
                ctypes.c_longlong: 8,
                ctypes.c_long: 4,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 8,
            }
            return type_to_size[value]

        def side_effect_ctypes_alignment(value):
            type_to_alignment = {
                ctypes.c_longlong: 8,
                ctypes.c_long: 4,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 8,
            }
            return type_to_alignment[value]

        ctypes_sizeof.side_effect = side_effect_ctypes_sizeof
        ctypes_alignment.side_effect = side_effect_ctypes_alignment

        fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
        ]
        BcmMsgHead = bcm_header_factory(fields)

        expected_fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
            # We expect 4 bytes of padding
            ("pad_0", ctypes.c_uint8),
            ("pad_1", ctypes.c_uint8),
            ("pad_2", ctypes.c_uint8),
            ("pad_3", ctypes.c_uint8),
        ]
        self.assertEqual(expected_fields, BcmMsgHead._fields_)

    @patch("ctypes.sizeof")
    @patch("ctypes.alignment")
    def test_bcm_header_factory_64_bit_sizeof_long_8_alignof_long_8(
        self, ctypes_sizeof, ctypes_alignment
    ):
        """This tests a 64-bit platform (ex. Ubuntu 18.04 on x86_64), where:

        * sizeof(long) == 8
        * sizeof(long long) == 8
        * alignof(long) == 8
        * alignof(long long) == 8
        """

        def side_effect_ctypes_sizeof(value):
            type_to_size = {
                ctypes.c_longlong: 8,
                ctypes.c_long: 8,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 8,
            }
            return type_to_size[value]

        def side_effect_ctypes_alignment(value):
            type_to_alignment = {
                ctypes.c_longlong: 8,
                ctypes.c_long: 8,
                ctypes.c_uint8: 1,
                ctypes.c_uint16: 2,
                ctypes.c_uint32: 4,
                ctypes.c_uint64: 8,
            }
            return type_to_alignment[value]

        ctypes_sizeof.side_effect = side_effect_ctypes_sizeof
        ctypes_alignment.side_effect = side_effect_ctypes_alignment

        fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
        ]
        BcmMsgHead = bcm_header_factory(fields)

        expected_fields = [
            ("opcode", ctypes.c_uint32),
            ("flags", ctypes.c_uint32),
            ("count", ctypes.c_uint32),
            # We expect 4 bytes of padding
            ("pad_0", ctypes.c_uint8),
            ("pad_1", ctypes.c_uint8),
            ("pad_2", ctypes.c_uint8),
            ("pad_3", ctypes.c_uint8),
            ("ival1_tv_sec", ctypes.c_long),
            ("ival1_tv_usec", ctypes.c_long),
            ("ival2_tv_sec", ctypes.c_long),
            ("ival2_tv_usec", ctypes.c_long),
            ("can_id", ctypes.c_uint32),
            ("nframes", ctypes.c_uint32),
        ]
        self.assertEqual(expected_fields, BcmMsgHead._fields_)

    def test_build_bcm_header(self):
        def _find_u32_fmt_char() -> str:
            for _fmt in ("H", "I", "L", "Q"):
                if struct.calcsize(_fmt) == 4:
                    return _fmt

        def _standard_size_little_endian_to_native(data: bytes) -> bytes:
            std_le_fmt = "<IIIllllII"
            native_fmt = "@" + std_le_fmt[1:].replace("I", _find_u32_fmt_char())
            aligned_data = struct.pack(native_fmt, *struct.unpack(std_le_fmt, data))
            padded_data = aligned_data + b"\x00" * ((8 - len(aligned_data) % 8) % 8)
            return padded_data

        expected_result = _standard_size_little_endian_to_native(
            b"\x02\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x00\x00\x00\x00"
            b"\x00\x00\x00\x00\x01\x04\x00\x00"
            b"\x01\x00\x00\x00"
        )

        self.assertEqual(
            expected_result,
            build_bcm_header(
                opcode=CAN_BCM_TX_DELETE,
                flags=0,
                count=0,
                ival1_seconds=0,
                ival1_usec=0,
                ival2_seconds=0,
                ival2_usec=0,
                can_id=0x401,
                nframes=1,
            ),
        )

    def test_build_bcm_tx_delete_header(self):
        can_id = 0x401
        flags = 0
        bcm_buffer = build_bcm_tx_delete_header(can_id=can_id, flags=flags)
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_DELETE, result.opcode)
        self.assertEqual(flags, result.flags)
        self.assertEqual(0, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(0, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_transmit_header_initial_period_0(self):
        can_id = 0x401
        flags = 0
        count = 42
        bcm_buffer = build_bcm_transmit_header(
            can_id=can_id,
            count=count,
            initial_period=0,
            subsequent_period=2,
            msg_flags=flags,
        )
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        # SETTIMER and STARTTIMER should be added to the initial flags
        self.assertEqual(flags | SETTIMER | STARTTIMER, result.flags)
        self.assertEqual(count, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(2, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_transmit_header_initial_period_1_24(self):
        can_id = 0x401
        flags = 0
        count = 42
        bcm_buffer = build_bcm_transmit_header(
            can_id=can_id,
            count=count,
            initial_period=1.24,
            subsequent_period=2,
            msg_flags=flags,
        )
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        # SETTIMER, STARTTIMER, TX_COUNTEVT should be added to the initial flags
        self.assertEqual(flags | SETTIMER | STARTTIMER | TX_COUNTEVT, result.flags)
        self.assertEqual(count, result.count)
        self.assertEqual(1, result.ival1_tv_sec)
        self.assertEqual(240000, result.ival1_tv_usec)
        self.assertEqual(2, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)

    def test_build_bcm_update_header(self):
        can_id = 0x401
        flags = 0
        bcm_buffer = build_bcm_update_header(can_id=can_id, msg_flags=flags)
        result = BcmMsgHead.from_buffer_copy(bcm_buffer)

        self.assertEqual(CAN_BCM_TX_SETUP, result.opcode)
        self.assertEqual(flags, result.flags)
        self.assertEqual(0, result.count)
        self.assertEqual(0, result.ival1_tv_sec)
        self.assertEqual(0, result.ival1_tv_usec)
        self.assertEqual(0, result.ival2_tv_sec)
        self.assertEqual(0, result.ival2_tv_usec)
        self.assertEqual(can_id, result.can_id)
        self.assertEqual(1, result.nframes)


if __name__ == "__main__":
    unittest.main()

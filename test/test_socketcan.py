"""
Test functions in `can.interfaces.socketcan.socketcan`.
"""
import unittest

try:
    from unittest.mock import Mock
    from unittest.mock import patch
    from unittest.mock import call
except ImportError:
    from mock import Mock
    from mock import patch
    from mock import call

import ctypes

from can.interfaces.socketcan.socketcan import bcm_header_factory


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
    def test_bcm_header_factory_32_bit_sizeof_long_4_alignof_long_8(
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
    def test_bcm_header_factory_64_bit_sizeof_long_4_alignof_long_4(
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


if __name__ == "__main__":
    unittest.main()

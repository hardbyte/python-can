#!/usr/bin/env python

"""
Tests helpers in `can.interfaces.socketcan.socketcan_common`.
"""

import gzip
import unittest
from base64 import b64decode
from unittest import mock

from can.interfaces.socketcan.utils import error_code_to_str, find_available_interfaces

from .config import IS_LINUX, TEST_INTERFACE_SOCKETCAN


class TestSocketCanHelpers(unittest.TestCase):
    @unittest.skipUnless(IS_LINUX, "socketcan is only available on Linux")
    def test_error_code_to_str(self):
        """
        Check that the function does not crash & always
        returns at least one character.
        """

        # all possible & also some invalid error codes
        test_data = list(range(0, 256)) + [-1, 256, 5235, 346264, None]

        for error_code in test_data:
            string = error_code_to_str(error_code)
            self.assertTrue(string)  # not None or empty

    @unittest.skipUnless(
        TEST_INTERFACE_SOCKETCAN, "socketcan is only available on Linux"
    )
    def test_find_available_interfaces(self):
        result = find_available_interfaces()

        self.assertGreaterEqual(len(result), 3)
        self.assertIn("vcan0", result)
        self.assertIn("vxcan0", result)
        self.assertIn("slcan0", result)

    def test_find_available_interfaces_w_patch(self):
        # Contains lo, eth0, wlan0, vcan0, mycustomCan123
        ip_output_gz_b64 = (
            "H4sIAAAAAAAAA+2UzW+CMBjG7/wVhrNL+BC29IboEqNSwzQejDEViiMC5aNsmmX/+wpZTGUwDAcP"
            "y5qmh+d5++bN80u7EXpsfZRnsUTf8yMXn0TQk/u8GqEQM1EMiMjpXoAOGZM3F6mUZxAuhoY55UpL"
            "fbWoKjO4Hts7pl/kLdc+pDlrrmuaqnNq4vqZU8wSkSTHOeYHIjFOM4poOevKmlpwbfF+4EfHkLil"
            "PRo/G6vZkrcPKcnjwnOxh/KA8h49JQGOimAkSaq03NFz/B0PiffIOfIXkeumOCtiEiUJXG++bp8S"
            "5Dooo/WVZeFnvxmYUgsM01fpBmQWfDAN256M7SqioQ2NkWm8LKvGnIU3qTN+xylrV/FdaHrJzmFk"
            "gkacozuzZMnhtAGkLANFAaoKBgOgaUDXG0F6Hrje7SDVWpDvAYpuIdmJV4dn2cSx9VUuGiFCe25Y"
            "fwTi4KmW4ptzG0ULGvYPLN1APSqdMN3/82TRtOeqSbW5hmcnzygJTRTJivofcEvAgrAVvgD8aLkv"
            "/AcAAA=="
        )
        ip_output = gzip.decompress(b64decode(ip_output_gz_b64)).decode("ascii")

        with mock.patch("subprocess.check_output") as check_output:
            check_output.return_value = ip_output
            ifs = find_available_interfaces()

            self.assertEqual(["vcan0", "mycustomCan123"], ifs)

    def test_find_available_interfaces_exception(self):
        with mock.patch("subprocess.check_output") as check_output:
            check_output.return_value = "<h1>Not JSON</h1>"
            result = find_available_interfaces()
            self.assertEqual([], result)

            check_output.side_effect = Exception("Something went wrong :-/")
            result = find_available_interfaces()
            self.assertEqual([], result)


if __name__ == "__main__":
    unittest.main()

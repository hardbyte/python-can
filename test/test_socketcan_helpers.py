#!/usr/bin/env python

"""
Tests helpers in `can.interfaces.socketcan.socketcan_common`.
"""

import unittest
from pathlib import Path
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
        ip_output = (Path(__file__).parent / "data" / "ip_link_list.json").read_text()

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

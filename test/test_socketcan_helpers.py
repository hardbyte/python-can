#!/usr/bin/env python
# coding: utf-8

"""
Tests helpers in `can.interfaces.socketcan.socketcan_common`.
"""

from __future__ import absolute_import

import unittest

from can.interfaces.socketcan.utils import \
    find_available_interfaces, error_code_to_str

from .config import *


class TestSocketCanHelpers(unittest.TestCase):

    @unittest.skipUnless(IS_LINUX, "socketcan is only available on Linux")
    def test_error_code_to_str(self):
        """
        Check that the function does not crash & always
        returns at least one character.
        """

        # all possible & also some invalid error codes
        test_data = list(range(0, 256)) + [-1, 256, 5235, 346264]

        for error_code in test_data:
            string = error_code_to_str(error_code)
            self.assertTrue(string) # not None or empty

    @unittest.skipUnless(IS_LINUX, "socketcan is only available on Linux")
    def test_find_available_interfaces(self):
        result = list(find_available_interfaces())
        self.assertGreaterEqual(len(result), 0)
        for entry in result:
            self.assertRegexpMatches(entry, r"v?can\d+")
        if IS_CI:
            self.assertGreaterEqual(len(result), 1)
            self.assertIn("vcan0", result)


if __name__ == '__main__':
    unittest.main()

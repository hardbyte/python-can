#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import absolute_import

import unittest

from .config import *
from can.interfaces.socketcan.socketcan_common import error_code_to_str

class TestSocketCanHelpers(unittest.TestCase):

    @unittest.skipUnless(IS_UNIX, "skip if not on UNIX")
    def test_error_code_to_str(self):
        """
        Check that the function does not crash & always
        returns a least one character.
        """

        # all possible & also some invalid error codes
        test_data = range(0, 256) + (-1, 256, 5235, 346264)

        for error_code in test_data:
            string = error_code_to_str(error_code)
            self.assertTrue(string) # not None or empty

if __name__ == '__main__':
    unittest.main()

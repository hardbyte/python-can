#!/usr/bin/env python
# coding: utf-8

"""
This module tests :meth:`can.BusABC._detect_available_configs` /
:meth:`can.BusABC.detect_available_configs`.
"""

import sys
import unittest

from can import detect_available_configs

if sys.version_info.major > 2:
    basestring = str


class TestDetectAvailableConfigs(unittest.TestCase):

    def test_count_returned(self):
        # At least virtual has to always return at least one interface
        self.assertGreaterEqual (len(detect_available_configs()                             ), 1)
        self.assertEquals       (len(detect_available_configs(search_only_in=[])            ), 0)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in='virtual')     ), 1)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in=['virtual'])   ), 1)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in=None)          ), 1)

    def test_general_values(self):
        returned = detect_available_configs()
        for config in returned:
            self.assertIn('interface', config)
            self.assertIn('channel', config)
            self.assertIsInstance(config['interface'], basestring)

    def test_content_virtual(self):
        returned = detect_available_configs(search_only_in='virtual')
        for config in returned:
            self.assertEqual(config['interface'], 'virtual')

if __name__ == '__main__':
    unittest.main()

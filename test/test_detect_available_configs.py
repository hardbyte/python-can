#!/usr/bin/env python
# coding: utf-8

"""
This module tests :meth:`can.BusABC._detect_available_configs` /
:meth:`can.BusABC.detect_available_configs`.
"""

from __future__ import absolute_import

import sys
import unittest
if sys.version_info.major > 2:
    basestring = str

from can import detect_available_configs

from .config import IS_LINUX


class TestDetectAvailableConfigs(unittest.TestCase):

    def test_count_returned(self):
        # At least virtual has to always return at least one interface
        self.assertGreaterEqual (len(detect_available_configs()                             ), 1)
        self.assertEquals       (len(detect_available_configs(search_only_in=[])            ), 0)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in='virtual')     ), 1)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in=['virtual'])   ), 1)
        self.assertGreaterEqual (len(detect_available_configs(search_only_in=None)          ), 1)

    def test_general_values(self):
        configs = detect_available_configs()
        for config in configs:
            self.assertIn('interface', config)
            self.assertIn('channel', config)
            self.assertIsInstance(config['interface'], basestring)

    def test_content_virtual(self):
        configs = detect_available_configs(search_only_in='virtual')
        for config in configs:
            self.assertEqual(config['interface'], 'virtual')

    def test_content_socketcan(self):
        configs = detect_available_configs(search_only_in='socketcan')
        for config in configs:
            self.assertIn(config['interface'], ('socketcan_native', 'socketcan_ctypes'))

    def test_socketcan_on_ci_server(self):
        configs = detect_available_configs(search_only_in='socketcan')
        self.assertGreaterEqual(len(configs), 1)
        self.assertIn('vcan0', [config['channel'] for config in configs])

    # see TestSocketCanHelpers.test_find_available_interfaces()


if __name__ == '__main__':
    unittest.main()

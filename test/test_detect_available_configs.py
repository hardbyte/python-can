#!/usr/bin/env python
# coding: utf-8

"""
This module tests :meth:`can.BusABC._detect_available_configs` and
:meth:`can.BusABC.detect_available_configs`.
"""

from __future__ import absolute_import

import sys
import unittest
if sys.version_info.major > 2:
    basestring = str

from can import detect_available_configs

from .config import IS_LINUX, IS_CI, TEST_INTERFACE_SOCKETCAN


class TestDetectAvailableConfigs(unittest.TestCase):

    def test_count_returned(self):
        # At least virtual has to always return at least one interface
        self.assertGreaterEqual (len(detect_available_configs()                         ), 1)
        self.assertEqual        (len(detect_available_configs(interfaces=[])            ), 0)
        self.assertGreaterEqual (len(detect_available_configs(interfaces='virtual')     ), 1)
        self.assertGreaterEqual (len(detect_available_configs(interfaces=['virtual'])   ), 1)
        self.assertGreaterEqual (len(detect_available_configs(interfaces=None)          ), 1)

    def test_general_values(self):
        configs = detect_available_configs()
        for config in configs:
            self.assertIn('interface', config)
            self.assertIn('channel', config)
            self.assertIsInstance(config['interface'], basestring)

    def test_content_virtual(self):
        configs = detect_available_configs(interfaces='virtual')
        for config in configs:
            self.assertEqual(config['interface'], 'virtual')

    def test_content_socketcan(self):
        configs = detect_available_configs(interfaces='socketcan')
        for config in configs:
            self.assertEqual(config['interface'], 'socketcan')

    @unittest.skipUnless(TEST_INTERFACE_SOCKETCAN, "socketcan is not tested")
    def test_socketcan_on_ci_server(self):
        configs = detect_available_configs(interfaces='socketcan')
        self.assertGreaterEqual(len(configs), 1)
        self.assertIn('vcan0', [config['channel'] for config in configs])

    # see TestSocketCanHelpers.test_find_available_interfaces() too


if __name__ == '__main__':
    unittest.main()

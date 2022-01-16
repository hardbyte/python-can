#!/usr/bin/env python

"""
This module tests :meth:`can.BusABC._detect_available_configs` and
:meth:`can.BusABC.detect_available_configs`.
"""

import unittest

from can import detect_available_configs

from .config import IS_CI, IS_UNIX, TEST_INTERFACE_SOCKETCAN


class TestDetectAvailableConfigs(unittest.TestCase):
    def test_count_returned(self):
        # At least virtual has to always return at least one interface
        self.assertGreaterEqual(len(detect_available_configs()), 1)
        self.assertEqual(len(detect_available_configs(interfaces=[])), 0)
        self.assertGreaterEqual(len(detect_available_configs(interfaces="virtual")), 1)
        self.assertGreaterEqual(
            len(detect_available_configs(interfaces=["virtual"])), 1
        )
        self.assertGreaterEqual(len(detect_available_configs(interfaces=None)), 1)

    def test_general_values(self):
        configs = detect_available_configs()
        for config in configs:
            self.assertIn("interface", config)
            self.assertIn("channel", config)

    def test_content_virtual(self):
        configs = detect_available_configs(interfaces="virtual")
        self.assertGreaterEqual(len(configs), 1)
        for config in configs:
            self.assertEqual(config["interface"], "virtual")

    def test_content_udp_multicast(self):
        configs = detect_available_configs(interfaces="udp_multicast")
        for config in configs:
            self.assertEqual(config["interface"], "udp_multicast")

    def test_content_socketcan(self):
        configs = detect_available_configs(interfaces="socketcan")
        for config in configs:
            self.assertEqual(config["interface"], "socketcan")

    def test_count_udp_multicast(self):
        configs = detect_available_configs(interfaces="udp_multicast")
        if IS_UNIX:
            self.assertGreaterEqual(len(configs), 2)
        else:
            self.assertEqual(len(configs), 0)

    @unittest.skipUnless(
        TEST_INTERFACE_SOCKETCAN and IS_CI, "this setup is very specific"
    )
    def test_socketcan_on_ci_server(self):
        configs = detect_available_configs(interfaces="socketcan")
        self.assertGreaterEqual(len(configs), 1)
        self.assertIn("vcan0", [config["channel"] for config in configs])

    # see TestSocketCanHelpers.test_find_available_interfaces() too


if __name__ == "__main__":
    unittest.main()

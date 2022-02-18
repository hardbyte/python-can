#!/usr/bin/env python

import unittest
import warnings

from can.util import _create_bus_config, _rename_kwargs


class RenameKwargsTest(unittest.TestCase):
    expected_kwargs = dict(a=1, b=2, c=3, d=4)

    def _test(self, kwargs, aliases):

        # Test that we do get the DeprecationWarning when called with deprecated kwargs
        with self.assertWarnsRegex(DeprecationWarning, "is deprecated"):
            _rename_kwargs("unit_test", kwargs, aliases)

        # Test that the aliases contains the deprecated values and
        # the obsolete kwargs have been removed
        assert kwargs == self.expected_kwargs

        # Test that we do not get a DeprecationWarning when we call
        # without deprecated kwargs

        # Cause all warnings to always be triggered.
        warnings.simplefilter("error", DeprecationWarning)
        try:
            _rename_kwargs("unit_test", kwargs, aliases)
        finally:
            warnings.resetwarnings()

    def test_rename(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4)
        aliases = {"old_a": "a", "old_b": "b"}
        self._test(kwargs, aliases)

    def test_obsolete(self):
        kwargs = dict(a=1, b=2, c=3, d=4, z=10)
        aliases = {"z": None}
        self._test(kwargs, aliases)

    def test_rename_and_obsolete(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        self._test(kwargs, aliases)

    def test_with_new_and_alias_present(self):
        kwargs = dict(old_a=1, a=1, b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        with self.assertRaises(TypeError):
            self._test(kwargs, aliases)


class TestBusConfig(unittest.TestCase):
    base_config = dict(interface="socketcan", bitrate=500_000)

    def test_timing_can_use_int(self):
        """
        Test that an exception is not raised when using
        integers for timing values in config.
        """
        timing_conf = dict(tseg1=5, tseg2=10, sjw=25)
        try:
            _create_bus_config({**self.base_config, **timing_conf})
        except TypeError as e:
            self.fail(e)

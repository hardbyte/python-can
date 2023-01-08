#!/usr/bin/env python

import unittest
import warnings

import pytest

from can.util import (
    _create_bus_config,
    _rename_kwargs,
    channel2int,
    deprecated_args_alias,
)


class RenameKwargsTest(unittest.TestCase):
    expected_kwargs = dict(a=1, b=2, c=3, d=4)

    def _test(self, start: str, end: str, kwargs, aliases):

        # Test that we do get the DeprecationWarning when called with deprecated kwargs
        with self.assertWarnsRegex(
            DeprecationWarning, "is deprecated.*?" + start + ".*?" + end
        ):
            _rename_kwargs("unit_test", start, end, kwargs, aliases)

        # Test that the aliases contains the deprecated values and
        # the obsolete kwargs have been removed
        assert kwargs == self.expected_kwargs

        # Test that we do not get a DeprecationWarning when we call
        # without deprecated kwargs

        # Cause all warnings to always be triggered.
        warnings.simplefilter("error", DeprecationWarning)
        try:
            _rename_kwargs("unit_test", start, end, kwargs, aliases)
        finally:
            warnings.resetwarnings()

    def test_rename(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4)
        aliases = {"old_a": "a", "old_b": "b"}
        self._test("1.0", "2.0", kwargs, aliases)

    def test_obsolete(self):
        kwargs = dict(a=1, b=2, c=3, d=4, z=10)
        aliases = {"z": None}
        self._test("1.0", "2.0", kwargs, aliases)

    def test_rename_and_obsolete(self):
        kwargs = dict(old_a=1, old_b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        self._test("1.0", "2.0", kwargs, aliases)

    def test_with_new_and_alias_present(self):
        kwargs = dict(old_a=1, a=1, b=2, c=3, d=4, z=10)
        aliases = {"old_a": "a", "old_b": "b", "z": None}
        with self.assertRaises(TypeError):
            self._test("1.0", "2.0", kwargs, aliases)


class DeprecatedArgsAliasTest(unittest.TestCase):
    def test_decorator(self):
        @deprecated_args_alias("1.0.0", old_a="a")
        def _test_func1(a):
            pass

        with pytest.warns(DeprecationWarning) as record:
            _test_func1(old_a=1)
            assert len(record) == 1
            assert (
                record[0].message.args[0]
                == "The 'old_a' argument is deprecated since python-can v1.0.0. Use 'a' instead."
            )

        @deprecated_args_alias("1.6.0", "3.4.0", old_a="a", old_b=None)
        def _test_func2(a):
            pass

        with pytest.warns(DeprecationWarning) as record:
            _test_func2(old_a=1, old_b=2)
            assert len(record) == 2
            assert record[0].message.args[0] == (
                "The 'old_a' argument is deprecated since python-can v1.6.0, and scheduled for "
                "removal in python-can v3.4.0. Use 'a' instead."
            )
            assert record[1].message.args[0] == (
                "The 'old_b' argument is deprecated since python-can v1.6.0, and scheduled for "
                "removal in python-can v3.4.0."
            )

        @deprecated_args_alias("1.6.0", "3.4.0", old_a="a")
        @deprecated_args_alias("2.0.0", "4.0.0", old_b=None)
        def _test_func3(a):
            pass

        with pytest.warns(DeprecationWarning) as record:
            _test_func3(old_a=1, old_b=2)
            assert len(record) == 2
            assert record[0].message.args[0] == (
                "The 'old_a' argument is deprecated since python-can v1.6.0, and scheduled "
                "for removal in python-can v3.4.0. Use 'a' instead."
            )
            assert record[1].message.args[0] == (
                "The 'old_b' argument is deprecated since python-can v2.0.0, and scheduled "
                "for removal in python-can v4.0.0."
            )

        with pytest.warns(DeprecationWarning) as record:
            _test_func3(old_a=1)
            assert len(record) == 1
            assert record[0].message.args[0] == (
                "The 'old_a' argument is deprecated since python-can v1.6.0, and scheduled "
                "for removal in python-can v3.4.0. Use 'a' instead."
            )

        with pytest.warns(DeprecationWarning) as record:
            _test_func3(a=1, old_b=2)
            assert len(record) == 1
            assert record[0].message.args[0] == (
                "The 'old_b' argument is deprecated since python-can v2.0.0, and scheduled "
                "for removal in python-can v4.0.0."
            )

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            _test_func3(a=1)


class TestBusConfig(unittest.TestCase):
    base_config = dict(interface="socketcan", bitrate=500_000)
    port_alpha_config = dict(interface="socketcan", bitrate=500_000, port="fail123")
    port_to_high_config = dict(interface="socketcan", bitrate=500_000, port="999999")
    port_wrong_type_config = dict(interface="socketcan", bitrate=500_000, port=(1234,))

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
        self.assertRaises(
            ValueError, _create_bus_config, {**self.port_alpha_config, **timing_conf}
        )
        self.assertRaises(
            ValueError, _create_bus_config, {**self.port_to_high_config, **timing_conf}
        )
        self.assertRaises(
            TypeError,
            _create_bus_config,
            {**self.port_wrong_type_config, **timing_conf},
        )


class TestChannel2Int(unittest.TestCase):
    def test_channel2int(self) -> None:
        self.assertEqual(0, channel2int("can0"))
        self.assertEqual(0, channel2int("vcan0"))
        self.assertEqual(1, channel2int("vcan1"))
        self.assertEqual(12, channel2int("vcan12"))
        self.assertEqual(3, channel2int(3))
        self.assertEqual(42, channel2int("42"))
        self.assertEqual(None, channel2int("can"))
        self.assertEqual(None, channel2int("can0a"))

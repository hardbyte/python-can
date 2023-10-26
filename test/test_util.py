#!/usr/bin/env python

import unittest
import warnings

import pytest

from can import BitTiming, BitTimingFd
from can.exceptions import CanInitializationError
from can.util import (
    _create_bus_config,
    _rename_kwargs,
    cast_from_string,
    channel2int,
    check_or_adjust_timing_clock,
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


class TestCheckAdjustTimingClock(unittest.TestCase):
    def test_adjust_timing(self):
        timing = BitTiming(f_clock=80_000_000, brp=10, tseg1=13, tseg2=2, sjw=1)

        # Check identity case
        new_timing = check_or_adjust_timing_clock(timing, valid_clocks=[80_000_000])
        assert timing == new_timing

        with pytest.warns(UserWarning) as record:
            new_timing = check_or_adjust_timing_clock(
                timing, valid_clocks=[8_000_000, 24_000_000]
            )
            assert len(record) == 1
            assert (
                record[0].message.args[0]
                == "Adjusted f_clock in BitTiming from 80000000 to 8000000"
            )
            assert new_timing.__class__ == BitTiming
            assert new_timing.f_clock == 8_000_000
            assert new_timing.bitrate == timing.bitrate
            assert new_timing.tseg1 == timing.tseg1
            assert new_timing.tseg2 == timing.tseg2
            assert new_timing.sjw == timing.sjw

        # Check that order is preserved
        with pytest.warns(UserWarning) as record:
            new_timing = check_or_adjust_timing_clock(
                timing, valid_clocks=[24_000_000, 8_000_000]
            )
            assert new_timing.f_clock == 24_000_000
            assert len(record) == 1
            assert (
                record[0].message.args[0]
                == "Adjusted f_clock in BitTiming from 80000000 to 24000000"
            )

        # Check that order is preserved for all valid clock rates
        with pytest.warns(UserWarning) as record:
            new_timing = check_or_adjust_timing_clock(
                timing, valid_clocks=[8_000, 24_000_000, 8_000_000]
            )
            assert new_timing.f_clock == 24_000_000
            assert len(record) == 1
            assert (
                record[0].message.args[0]
                == "Adjusted f_clock in BitTiming from 80000000 to 24000000"
            )

        with pytest.raises(CanInitializationError):
            check_or_adjust_timing_clock(timing, valid_clocks=[8_000, 16_000])

    def test_adjust_timing_fd(self):
        timing = BitTimingFd(
            f_clock=160_000_000,
            nom_brp=2,
            nom_tseg1=119,
            nom_tseg2=40,
            nom_sjw=40,
            data_brp=2,
            data_tseg1=29,
            data_tseg2=10,
            data_sjw=10,
        )

        # Check identity case
        new_timing = check_or_adjust_timing_clock(timing, valid_clocks=[160_000_000])
        assert timing == new_timing

        with pytest.warns(UserWarning) as record:
            new_timing = check_or_adjust_timing_clock(
                timing, valid_clocks=[8_000, 80_000_000]
            )
            assert len(record) == 1, "; ".join(
                [record[i].message.args[0] for i in range(len(record))]
            )  # print all warnings, if more than one warning is present
            assert (
                record[0].message.args[0]
                == "Adjusted f_clock in BitTimingFd from 160000000 to 80000000"
            )
            assert new_timing.__class__ == BitTimingFd
            assert new_timing.f_clock == 80_000_000
            assert new_timing.nom_bitrate == timing.nom_bitrate
            assert new_timing.nom_sample_point == timing.nom_sample_point
            assert new_timing.data_bitrate == timing.data_bitrate
            assert new_timing.data_sample_point == timing.data_sample_point

        with pytest.raises(CanInitializationError):
            check_or_adjust_timing_clock(timing, valid_clocks=[8_000, 16_000])


class TestCastFromString(unittest.TestCase):
    def test_cast_from_string(self) -> None:
        self.assertEqual(1, cast_from_string("1"))
        self.assertEqual(-1, cast_from_string("-1"))
        self.assertEqual(0, cast_from_string("-0"))
        self.assertEqual(1.1, cast_from_string("1.1"))
        self.assertEqual(-1.1, cast_from_string("-1.1"))
        self.assertEqual(0.1, cast_from_string(".1"))
        self.assertEqual(10.0, cast_from_string(".1e2"))
        self.assertEqual(0.001, cast_from_string(".1e-2"))
        self.assertEqual(-0.001, cast_from_string("-.1e-2"))
        self.assertEqual("text", cast_from_string("text"))
        self.assertEqual("", cast_from_string(""))
        self.assertEqual("can0", cast_from_string("can0"))
        self.assertEqual("0can", cast_from_string("0can"))
        self.assertEqual(False, cast_from_string("false"))
        self.assertEqual(False, cast_from_string("False"))
        self.assertEqual(True, cast_from_string("true"))
        self.assertEqual(True, cast_from_string("True"))

        with self.assertRaises(TypeError):
            cast_from_string(None)

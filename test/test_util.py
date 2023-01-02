#!/usr/bin/env python

import unittest
import warnings

import pytest

from can import BitTiming, BitTimingFd
from can.util import (
    _create_bus_config,
    _rename_kwargs,
    channel2int,
    check_or_adjust_timing_clock,
)
from can.exceptions import CanInitializationError


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
        timing = BitTiming(
            f_clock=80_000_000, bitrate=500_000, tseg1=13, tseg2=2, sjw=1
        )

        # Check identity case
        new_timing = check_or_adjust_timing_clock(timing, valid_clocks=[80_000_000])
        assert timing == new_timing

        new_timing = check_or_adjust_timing_clock(
            timing, valid_clocks=[8_000_000, 24_000_000]
        )

        assert new_timing.__class__ == BitTiming
        assert new_timing.f_clock == 8_000_000
        assert new_timing.bitrate == timing.bitrate
        assert new_timing.tseg1 == timing.tseg1
        assert new_timing.tseg2 == timing.tseg2
        assert new_timing.sjw == timing.sjw

        # Check that order is preserved
        new_timing = check_or_adjust_timing_clock(
            timing, valid_clocks=[24_000_000, 8_000_000]
        )
        assert new_timing.f_clock == 24_000_000

        # Check that order is preserved for all valid clock rates
        new_timing = check_or_adjust_timing_clock(
            timing, valid_clocks=[8_000, 24_000_000, 8_000_000]
        )
        assert new_timing.f_clock == 24_000_000

        with pytest.raises(CanInitializationError):
            check_or_adjust_timing_clock(timing, valid_clocks=[8_000, 16_000])

    def test_adjust_timing_fd(self):
        timing = BitTimingFd(
            f_clock=160_000_000,
            nom_bitrate=500_000,
            nom_tseg1=119,
            nom_tseg2=40,
            nom_sjw=40,
            data_bitrate=2_000_000,
            data_tseg1=29,
            data_tseg2=10,
            data_sjw=10,
        )

        # Check identity case
        new_timing = check_or_adjust_timing_clock(timing, valid_clocks=[160_000_000])
        assert timing == new_timing

        new_timing = check_or_adjust_timing_clock(
            timing, valid_clocks=[8_000, 80_000_000]
        )
        assert new_timing.__class__ == BitTimingFd
        assert new_timing.f_clock == 80_000_000
        assert new_timing.nom_bitrate == 500_000
        assert new_timing.nom_tseg1 == 119
        assert new_timing.nom_tseg2 == 40
        assert new_timing.nom_sjw == 40
        assert new_timing.data_bitrate == 2_000_000
        assert new_timing.data_tseg1 == 29
        assert new_timing.data_tseg2 == 10
        assert new_timing.data_sjw == 10

        with pytest.raises(CanInitializationError):
            check_or_adjust_timing_clock(timing, valid_clocks=[8_000, 16_000])

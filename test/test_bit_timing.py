#!/usr/bin/env python

import struct

import pytest

import can
from can.interfaces.pcan.pcan import PCAN_BITRATES


def test_sja1000():
    """Test some values obtained using other bit timing calculators."""
    timing = can.BitTiming(
        f_clock=8_000_000, brp=4, tseg1=11, tseg2=4, sjw=2, nof_samples=3, strict=True
    )
    assert timing.f_clock == 8_000_000
    assert timing.bitrate == 125_000
    assert timing.brp == 4
    assert timing.nbt == 16
    assert timing.tseg1 == 11
    assert timing.tseg2 == 4
    assert timing.sjw == 2
    assert timing.nof_samples == 3
    assert timing.sample_point == 75
    assert timing.btr0 == 0x43
    assert timing.btr1 == 0xBA

    timing = can.BitTiming(
        f_clock=8_000_000, brp=1, tseg1=13, tseg2=2, sjw=1, strict=True
    )
    assert timing.f_clock == 8_000_000
    assert timing.bitrate == 500_000
    assert timing.brp == 1
    assert timing.nbt == 16
    assert timing.tseg1 == 13
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.nof_samples == 1
    assert timing.sample_point == 87.5
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x1C

    timing = can.BitTiming(
        f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1, strict=True
    )
    assert timing.f_clock == 8_000_000
    assert timing.bitrate == 1_000_000
    assert timing.brp == 1
    assert timing.nbt == 8
    assert timing.tseg1 == 5
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.nof_samples == 1
    assert timing.sample_point == 75
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x14


def test_from_bitrate_and_segments():
    timing = can.BitTiming.from_bitrate_and_segments(
        f_clock=8_000_000, bitrate=125_000, tseg1=11, tseg2=4, sjw=2, nof_samples=3
    )
    assert timing == can.BitTiming(
        f_clock=8_000_000, brp=4, tseg1=11, tseg2=4, sjw=2, nof_samples=3
    )

    timing = can.BitTiming.from_bitrate_and_segments(
        f_clock=8_000_000, bitrate=500_000, tseg1=13, tseg2=2, sjw=1
    )
    assert timing == can.BitTiming(f_clock=8_000_000, brp=1, tseg1=13, tseg2=2, sjw=1)

    timing = can.BitTiming.from_bitrate_and_segments(
        f_clock=8_000_000, bitrate=1_000_000, tseg1=5, tseg2=2, sjw=1, strict=True
    )
    assert timing == can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)

    timing = can.BitTimingFd.from_bitrate_and_segments(
        f_clock=80_000_000,
        nom_bitrate=500_000,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_bitrate=2_000_000,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    assert timing == can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )


def test_can_fd():
    # test non-strict
    timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )

    assert timing.f_clock == 80_000_000
    assert timing.nom_bitrate == 500_000
    assert timing.nom_brp == 1
    assert timing.nbt == 160
    assert timing.nom_tseg1 == 119
    assert timing.nom_tseg2 == 40
    assert timing.nom_sjw == 40
    assert timing.nom_sample_point == 75
    assert timing.data_bitrate == 2_000_000
    assert timing.data_brp == 1
    assert timing.dbt == 40
    assert timing.data_tseg1 == 29
    assert timing.data_tseg2 == 10
    assert timing.data_sjw == 10
    assert timing.data_sample_point == 75

    # test strict valid
    timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=2,
        nom_tseg1=59,
        nom_tseg2=20,
        nom_sjw=20,
        data_brp=2,
        data_tseg1=14,
        data_tseg2=5,
        data_sjw=5,
        strict=True,
    )
    assert timing.f_clock == 80_000_000
    assert timing.nom_bitrate == 500_000
    assert timing.nom_brp == 2
    assert timing.nbt == 80
    assert timing.nom_tseg1 == 59
    assert timing.nom_tseg2 == 20
    assert timing.nom_sjw == 20
    assert timing.nom_sample_point == 75
    assert timing.data_bitrate == 2_000_000
    assert timing.data_brp == 2
    assert timing.dbt == 20
    assert timing.data_tseg1 == 14
    assert timing.data_tseg2 == 5
    assert timing.data_sjw == 5
    assert timing.data_sample_point == 75


@pytest.mark.parametrize(
    ("btr0", "btr1"),
    [(0x100, 0x14), (0x00, 0x100), (-1, 0x14), (0x00, -1)],
)
def test_from_btr_out_of_range(btr0: int, btr1: int) -> None:
    """
    Test Scope:
        BitTiming.from_registers rejects register values that do not fit into 8 bits.
    Preconditions:
        None.
    Events:
        Call BitTiming.from_registers with btr0 or btr1 outside of 0...255.
    Evaluate:
        A ValueError is raised.
    """
    with pytest.raises(ValueError):
        can.BitTiming.from_registers(f_clock=8_000_000, btr0=btr0, btr1=btr1)


def test_btr_persistence():
    f_clock = 8_000_000
    for btr0btr1 in PCAN_BITRATES.values():
        btr0, btr1 = struct.pack(">H", btr0btr1.value)

        t = can.BitTiming.from_registers(f_clock, btr0, btr1)
        assert t.btr0 == btr0
        assert t.btr1 == btr1


def test_from_sample_point():
    timing = can.BitTiming.from_sample_point(
        f_clock=16_000_000,
        bitrate=500_000,
        sample_point=69.0,
    )
    assert timing.f_clock == 16_000_000
    assert timing.bitrate == 500_000
    assert 68 < timing.sample_point < 70

    fd_timing = can.BitTimingFd.from_sample_point(
        f_clock=80_000_000,
        nom_bitrate=1_000_000,
        nom_sample_point=75.0,
        data_bitrate=8_000_000,
        data_sample_point=70.0,
    )
    assert fd_timing.f_clock == 80_000_000
    assert fd_timing.nom_bitrate == 1_000_000
    assert 74 < fd_timing.nom_sample_point < 76
    assert fd_timing.data_bitrate == 8_000_000
    assert 69 < fd_timing.data_sample_point < 71


def test_iterate_from_sample_point():
    for sp in range(50, 100):
        solutions = list(
            can.BitTiming.iterate_from_sample_point(
                f_clock=16_000_000,
                bitrate=500_000,
                sample_point=sp,
            )
        )
        assert len(solutions) >= 2

    for nsp in range(50, 100, 7):
        for dsp in range(50, 100, 7):
            solutions = list(
                can.BitTimingFd.iterate_from_sample_point(
                    f_clock=80_000_000,
                    nom_bitrate=500_000,
                    nom_sample_point=nsp,
                    data_bitrate=2_000_000,
                    data_sample_point=dsp,
                )
            )

            assert len(solutions) >= 2


def test_equality():
    t1 = can.BitTiming.from_registers(f_clock=8_000_000, btr0=0x00, btr1=0x14)
    t2 = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1, nof_samples=1)
    t3 = can.BitTiming(
        f_clock=16_000_000, brp=2, tseg1=5, tseg2=2, sjw=1, nof_samples=1
    )
    assert t1 == t2
    assert t1 != t3
    assert t2 != t3
    assert t1 != 10

    t4 = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    t5 = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    t6 = can.BitTimingFd.from_sample_point(
        f_clock=80_000_000,
        nom_bitrate=1_000_000,
        nom_sample_point=75.0,
        data_bitrate=8_000_000,
        data_sample_point=70.0,
    )
    assert t4 == t5
    assert t4 != t6
    assert t4 != t1


def test_string_representation():
    timing = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)
    assert str(timing) == (
        "BR: 1_000_000 bit/s, SP: 75.00%, BRP: 1, TSEG1: 5, TSEG2: 2, SJW: 1, "
        "BTR: 0014h, CLK: 8MHz"
    )

    fd_timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    assert str(fd_timing) == (
        "NBR: 500_000 bit/s, NSP: 75.00%, NBRP: 1, NTSEG1: 119, NTSEG2: 40, NSJW: 40, "
        "DBR: 2_000_000 bit/s, DSP: 75.00%, DBRP: 1, DTSEG1: 29, DTSEG2: 10, DSJW: 10, "
        "CLK: 80MHz"
    )


def test_repr():
    timing = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)
    assert repr(timing) == (
        "can.BitTiming(f_clock=8000000, brp=1, tseg1=5, tseg2=2, sjw=1, nof_samples=1)"
    )

    fd_timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    assert repr(fd_timing) == (
        "can.BitTimingFd(f_clock=80000000, nom_brp=1, nom_tseg1=119, nom_tseg2=40, "
        "nom_sjw=40, data_brp=1, data_tseg1=29, data_tseg2=10, data_sjw=10)"
    )


def test_hash():
    _timings = {
        can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1, nof_samples=1),
        can.BitTimingFd(
            f_clock=80_000_000,
            nom_brp=1,
            nom_tseg1=119,
            nom_tseg2=40,
            nom_sjw=40,
            data_brp=1,
            data_tseg1=29,
            data_tseg2=10,
            data_sjw=10,
        ),
    }
    for timing in list(_timings):
        assert type(timing)(**dict(timing)) in _timings


def test_mapping():
    timing = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)
    timing_dict = dict(timing)
    assert timing == can.BitTiming(**timing_dict)

    fd_timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=1,
        nom_tseg1=119,
        nom_tseg2=40,
        nom_sjw=40,
        data_brp=1,
        data_tseg1=29,
        data_tseg2=10,
        data_sjw=10,
    )
    fd_timing_dict = dict(fd_timing)
    assert fd_timing == can.BitTimingFd(**fd_timing_dict)


def test_oscillator_tolerance():
    timing = can.BitTiming(f_clock=16_000_000, brp=2, tseg1=10, tseg2=5, sjw=4)
    osc_tol = timing.oscillator_tolerance(
        node_loop_delay_ns=250,
        bus_length_m=10.0,
    )
    assert osc_tol == pytest.approx(1.23, abs=1e-2)

    fd_timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=5,
        nom_tseg1=27,
        nom_tseg2=4,
        nom_sjw=4,
        data_brp=5,
        data_tseg1=6,
        data_tseg2=1,
        data_sjw=1,
    )
    osc_tol = fd_timing.oscillator_tolerance(
        node_loop_delay_ns=250,
        bus_length_m=10.0,
    )
    assert osc_tol == pytest.approx(0.48, abs=1e-2)


def test_recreate_with_f_clock():
    timing_8mhz = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)
    timing_16mhz = timing_8mhz.recreate_with_f_clock(f_clock=16_000_000)
    assert timing_8mhz.bitrate == timing_16mhz.bitrate
    assert timing_8mhz.sample_point == timing_16mhz.sample_point
    assert (timing_8mhz.sjw / timing_8mhz.nbt) == pytest.approx(
        timing_16mhz.sjw / timing_16mhz.nbt, abs=1e-3
    )
    assert timing_8mhz.nof_samples == timing_16mhz.nof_samples

    timing_16mhz = can.BitTiming(
        f_clock=16000000, brp=2, tseg1=12, tseg2=3, sjw=3, nof_samples=1
    )
    timing_8mhz = timing_16mhz.recreate_with_f_clock(f_clock=8_000_000)
    assert timing_8mhz.bitrate == timing_16mhz.bitrate
    assert timing_8mhz.sample_point == timing_16mhz.sample_point
    assert (timing_8mhz.sjw / timing_8mhz.nbt) == pytest.approx(
        timing_16mhz.sjw / timing_16mhz.nbt, abs=1e-2
    )
    assert timing_8mhz.nof_samples == timing_16mhz.nof_samples

    fd_timing_80mhz = can.BitTimingFd(
        f_clock=80_000_000,
        nom_brp=5,
        nom_tseg1=27,
        nom_tseg2=4,
        nom_sjw=4,
        data_brp=5,
        data_tseg1=6,
        data_tseg2=1,
        data_sjw=1,
    )
    fd_timing_60mhz = fd_timing_80mhz.recreate_with_f_clock(f_clock=60_000_000)
    assert fd_timing_80mhz.nom_bitrate == fd_timing_60mhz.nom_bitrate
    assert fd_timing_80mhz.nom_sample_point == pytest.approx(
        fd_timing_60mhz.nom_sample_point, abs=1.0
    )
    assert (fd_timing_80mhz.nom_sjw / fd_timing_80mhz.nbt) == pytest.approx(
        fd_timing_60mhz.nom_sjw / fd_timing_60mhz.nbt, abs=1e-2
    )
    assert fd_timing_80mhz.data_bitrate == fd_timing_60mhz.data_bitrate
    assert fd_timing_80mhz.data_sample_point == pytest.approx(
        fd_timing_60mhz.data_sample_point, abs=1.0
    )
    assert (fd_timing_80mhz.data_sjw / fd_timing_80mhz.dbt) == pytest.approx(
        fd_timing_60mhz.data_sjw / fd_timing_60mhz.dbt, abs=1e-2
    )


_CLASSIC_KWARGS = {"f_clock": 8_000_000, "brp": 1, "tseg1": 5, "tseg2": 2, "sjw": 1}
_FD_KWARGS = {
    "f_clock": 80_000_000,
    "nom_brp": 1,
    "nom_tseg1": 59,
    "nom_tseg2": 20,
    "nom_sjw": 10,
    "data_brp": 1,
    "data_tseg1": 6,
    "data_tseg2": 3,
    "data_sjw": 2,
}


@pytest.mark.parametrize(
    ("cls", "base", "overrides", "match"),
    [
        (can.BitTiming, _CLASSIC_KWARGS, {"f_clock": 0}, "f_clock"),
        (can.BitTiming, _CLASSIC_KWARGS, {"brp": 0}, "brp"),
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg1": 0}, "tseg1"),
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg2": 0}, "tseg2"),
        (can.BitTiming, _CLASSIC_KWARGS, {"sjw": 0}, "sjw"),
        (can.BitTiming, _CLASSIC_KWARGS, {"sjw": 3}, "tseg2"),
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg1": 1, "tseg2": 4, "sjw": 2}, "tseg1"),
        (can.BitTiming, _CLASSIC_KWARGS, {"nof_samples": 2}, "nof_samples"),
        (can.BitTimingFd, _FD_KWARGS, {"f_clock": 0}, "f_clock"),
        (can.BitTimingFd, _FD_KWARGS, {"nom_brp": 0}, "nom_brp"),
        (can.BitTimingFd, _FD_KWARGS, {"nom_tseg2": 0}, "nom_tseg2"),
        (can.BitTimingFd, _FD_KWARGS, {"nom_sjw": 21}, "nom_tseg2"),
        (can.BitTimingFd, _FD_KWARGS, {"data_sjw": 0}, "data_sjw"),
        (
            can.BitTimingFd,
            _FD_KWARGS,
            {"data_tseg1": 1, "data_tseg2": 8, "data_sjw": 2},
            "data_tseg1",
        ),
    ],
)
def test_invalid_structure(cls, base, overrides, match) -> None:
    """
    Test Scope:
        BitTiming and BitTimingFd reject structurally invalid parameters,
        also when strict is False.
    Preconditions:
        A valid set of constructor arguments for the respective class.
    Events:
        Construct the class with one or more arguments replaced by an invalid value.
    Evaluate:
        A ValueError naming the offending parameter is raised.
    """
    with pytest.raises(ValueError, match=match):
        cls(**{**base, **overrides})


@pytest.mark.parametrize(
    ("overrides", "register"),
    [
        ({"brp": 100}, "btr0"),
        ({"tseg1": 10, "tseg2": 5, "sjw": 5}, "btr0"),
        ({"tseg1": 20}, "btr1"),
        ({"tseg1": 10, "tseg2": 9}, "btr1"),
    ],
)
def test_btr_not_encodable(overrides, register) -> None:
    """
    Test Scope:
        A non-strict BitTiming with values beyond the SJA1000 register range
        can be created, but cannot be converted to BTR registers.
    Preconditions:
        None.
    Events:
        Construct a non-strict BitTiming with brp, sjw, tseg1 or tseg2 out of
        register range, read the register property and convert the timing to str.
    Evaluate:
        The register property raises a ValueError and the string representation
        shows "BTR: n/a".
    """
    timing = can.BitTiming(**{**_CLASSIC_KWARGS, **overrides})
    with pytest.raises(ValueError):
        getattr(timing, register)
    assert "BTR: n/a" in str(timing)


@pytest.mark.parametrize(
    "create",
    [
        lambda: can.BitTiming.from_bitrate_and_segments(
            f_clock=8_000_000, bitrate=0, tseg1=5, tseg2=2, sjw=1
        ),
        lambda: can.BitTiming.from_sample_point(f_clock=8_000_000, bitrate=-1),
        lambda: list(
            can.BitTiming.iterate_from_sample_point(f_clock=8_000_000, bitrate=0)
        ),
        lambda: can.BitTimingFd.from_bitrate_and_segments(
            f_clock=80_000_000,
            nom_bitrate=0,
            nom_tseg1=59,
            nom_tseg2=20,
            nom_sjw=10,
            data_bitrate=8_000_000,
            data_tseg1=6,
            data_tseg2=3,
            data_sjw=2,
        ),
        lambda: can.BitTimingFd.from_sample_point(
            f_clock=80_000_000,
            nom_bitrate=500_000,
            nom_sample_point=80.0,
            data_bitrate=-1,
            data_sample_point=80.0,
        ),
        lambda: list(
            can.BitTimingFd.iterate_from_sample_point(
                f_clock=80_000_000,
                nom_bitrate=0,
                nom_sample_point=80.0,
                data_bitrate=2_000_000,
                data_sample_point=80.0,
            )
        ),
    ],
    ids=[
        "from_bitrate_and_segments",
        "from_sample_point",
        "iterate_from_sample_point",
        "fd_from_bitrate_and_segments",
        "fd_from_sample_point",
        "fd_iterate_from_sample_point",
    ],
)
def test_invalid_bitrate(create) -> None:
    """
    Test Scope:
        The factory methods and solvers reject bitrates that are not positive.
    Preconditions:
        None.
    Events:
        Call a factory method or solver with a bitrate of 0 or below.
    Evaluate:
        A ValueError naming the bitrate is raised.
    """
    with pytest.raises(ValueError, match="bitrate"):
        create()


@pytest.mark.parametrize(
    ("cls", "base", "overrides", "match"),
    [
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg1": 1, "tseg2": 6}, "tseg1"),
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg1": 6, "tseg2": 1}, "tseg2"),
        (
            can.BitTiming,
            _CLASSIC_KWARGS,
            {"tseg1": 2, "tseg2": 5, "sjw": 2},
            "propagation",
        ),
        (can.BitTiming, _CLASSIC_KWARGS, {"tseg1": 2, "tseg2": 5}, "sample point"),
        (
            can.BitTiming,
            _CLASSIC_KWARGS,
            {"f_clock": 264_000_000, "brp": 33},
            "prescaler",
        ),
        (can.BitTimingFd, _FD_KWARGS, {"nom_brp": 33, "data_brp": 33}, "nom_brp"),
        (
            can.BitTimingFd,
            _FD_KWARGS,
            {"nom_tseg1": 119, "nom_tseg2": 40, "nom_sjw": 40},
            "Nominal bit time",
        ),
        (can.BitTimingFd, _FD_KWARGS, {"nom_brp": 32, "data_brp": 33}, "data_brp"),
        (
            can.BitTimingFd,
            _FD_KWARGS,
            {"nom_tseg1": 10, "nom_tseg2": 10, "nom_sjw": 10},
            "propagation",
        ),
        (
            can.BitTimingFd,
            _FD_KWARGS,
            {"nom_tseg1": 9, "nom_tseg2": 12, "nom_sjw": 5},
            "arbitration sample point",
        ),
        (
            can.BitTimingFd,
            _FD_KWARGS,
            {"data_tseg1": 2, "data_tseg2": 5, "data_sjw": 2},
            "data sample point",
        ),
    ],
)
def test_strict_ranges(cls, base, overrides, match) -> None:
    """
    Test Scope:
        With strict=True, BitTiming and BitTimingFd reject timings outside the
        minimum configuration ranges of ISO 11898-1 and sample points below 50%.
    Preconditions:
        A set of constructor arguments that is valid in strict mode.
    Events:
        Construct the class with strict=True and one or more arguments replaced
        by a value outside of the strict range.
    Evaluate:
        A ValueError naming the violated rule is raised.
    """
    with pytest.raises(ValueError, match=match):
        cls(**{**base, **overrides}, strict=True)


@pytest.mark.parametrize(
    ("cls", "kwargs", "sample_point_attr"),
    [
        (can.BitTiming, {**_CLASSIC_KWARGS, "tseg1": 2, "tseg2": 5}, "sample_point"),
        (
            can.BitTimingFd,
            {**_FD_KWARGS, "nom_tseg1": 9, "nom_tseg2": 12, "nom_sjw": 5},
            "nom_sample_point",
        ),
        (
            can.BitTimingFd,
            {**_FD_KWARGS, "data_tseg1": 2, "data_tseg2": 5, "data_sjw": 2},
            "data_sample_point",
        ),
    ],
)
def test_non_strict_allows_low_sample_point(cls, kwargs, sample_point_attr) -> None:
    """
    Test Scope:
        Without strict mode, sample points below 50% are accepted, since
        ISO 11898-1 does not restrict the position of the sample point.
    Preconditions:
        None.
    Events:
        Construct the class with strict=False and segments that place the
        sample point below 50%.
    Evaluate:
        The instance is created and reports the sample point below 50%.
    """
    timing = cls(**kwargs)
    assert getattr(timing, sample_point_attr) < 50.0


def test_from_sample_point_follows_strict_rules() -> None:
    """
    Test Scope:
        The solvers only return timings that fulfil the strict rules for
        tseg2 and SJW, also when the requested sample point cannot be reached.
    Preconditions:
        None.
    Events:
        Call BitTiming.from_sample_point for sample points from 50% to 99% and
        BitTimingFd.from_sample_point for sample points from 50% to 99% in steps of 7%.
    Evaluate:
        tseg2 is at least 2 for classic CAN and SJW is less than tseg1 for
        classic CAN and the arbitration phase of CAN FD.
    """
    for sp in range(50, 100):
        timing = can.BitTiming.from_sample_point(
            f_clock=8_000_000, bitrate=1_000_000, sample_point=sp
        )
        assert timing.tseg2 >= 2
        assert timing.sjw <= timing.tseg1 - 1

    for sp in range(50, 100, 7):
        fd_timing = can.BitTimingFd.from_sample_point(
            f_clock=80_000_000,
            nom_bitrate=500_000,
            nom_sample_point=sp,
            data_bitrate=2_000_000,
            data_sample_point=sp,
        )
        assert fd_timing.nom_sjw <= fd_timing.nom_tseg1 - 1


def test_from_sample_point_prefers_accurate_bitrate() -> None:
    """
    Test Scope:
        BitTiming.from_sample_point finds solutions whose prescaler and bit time
        only match the requested bitrate within the tolerance, and prefers an
        exact bitrate over a closer sample point.
    Preconditions:
        None.
    Events:
        Request 12 kbit/s and 20 kbit/s from an 8 MHz clock.
    Evaluate:
        A 12 kbit/s timing within the tolerance of 1/256 is found. The 20 kbit/s
        timing matches the requested bitrate exactly, although another candidate
        is closer to the requested sample point.
    """
    timing = can.BitTiming.from_sample_point(
        f_clock=8_000_000, bitrate=12_000, sample_point=75.0
    )
    assert abs(timing.bitrate - 12_000) <= 12_000 / 256

    candidates = list(
        can.BitTiming.iterate_from_sample_point(
            f_clock=8_000_000, bitrate=20_000, sample_point=61.0
        )
    )
    timing = can.BitTiming.from_sample_point(
        f_clock=8_000_000, bitrate=20_000, sample_point=61.0
    )
    assert timing.f_clock / (timing.nbt * timing.brp) == 20_000
    assert any(
        abs(c.sample_point - 61.0) < abs(timing.sample_point - 61.0) for c in candidates
    )


@pytest.mark.parametrize("sample_point", [100.0, 150.0])
@pytest.mark.parametrize(
    "create",
    [
        lambda sp: can.BitTiming.from_sample_point(
            f_clock=8_000_000, bitrate=500_000, sample_point=sp
        ),
        lambda sp: list(
            can.BitTiming.iterate_from_sample_point(
                f_clock=8_000_000, bitrate=500_000, sample_point=sp
            )
        ),
        lambda sp: can.BitTimingFd.from_sample_point(
            f_clock=80_000_000,
            nom_bitrate=500_000,
            nom_sample_point=sp,
            data_bitrate=2_000_000,
            data_sample_point=80.0,
        ),
        lambda sp: list(
            can.BitTimingFd.iterate_from_sample_point(
                f_clock=80_000_000,
                nom_bitrate=500_000,
                nom_sample_point=80.0,
                data_bitrate=2_000_000,
                data_sample_point=sp,
            )
        ),
    ],
    ids=[
        "from_sample_point",
        "iterate_from_sample_point",
        "fd_from_sample_point",
        "fd_iterate_from_sample_point",
    ],
)
def test_sample_point_too_high(create, sample_point) -> None:
    """
    Test Scope:
        The solvers reject sample points of 100% or more.
    Preconditions:
        None.
    Events:
        Call a solver with a sample point of 100% or above.
    Evaluate:
        A ValueError naming the sample point is raised.
    """
    with pytest.raises(ValueError, match="sample_point"):
        create(sample_point)


def test_oscillator_tolerance_exact_time_quantum() -> None:
    """
    Test Scope:
        BitTiming.oscillator_tolerance uses the exact time quantum, also when it
        is not an integer number of nanoseconds.
    Preconditions:
        None.
    Events:
        Calculate the oscillator tolerance of an 80 MHz timing with brp=1
        (time quantum 12.5 ns), tseg1=63, tseg2=16 and sjw=16 for a node loop
        delay of 250 ns and a bus length of 10 m.
    Evaluate:
        The round trip delay of 600 ns needs 48 time quanta of propagation
        segment, leaving Phase_Seg1 = 15. The limiting condition is then
        min(Phase_Seg1, Phase_Seg2) / (2 * (13 * nbt - Phase_Seg2)) = 15 / 2048.
    """
    timing = can.BitTiming(f_clock=80_000_000, brp=1, tseg1=63, tseg2=16, sjw=16)
    osc_tol = timing.oscillator_tolerance(node_loop_delay_ns=250, bus_length_m=10.0)
    assert osc_tol == pytest.approx(100 * 15 / 2048)


def test_fd_from_sample_point_prefers_accurate_bitrate() -> None:
    """
    Test Scope:
        BitTimingFd.from_sample_point prefers an accurate bitrate over a shared
        prescaler, and a shared prescaler over a closer sample point.
    Preconditions:
        None.
    Events:
        Request 250 kbit/s / 1.212121 Mbit/s from an 80 MHz clock, where only
        separate prescalers give an exact nominal bitrate. Request 125 kbit/s /
        1 Mbit/s from a 20 MHz clock, where separate prescalers would reach the
        requested sample points more closely.
    Evaluate:
        The first timing has the exact nominal bitrate. The second timing uses
        the same prescaler for both phases, although an exact candidate with
        separate prescalers is closer to the requested sample points.
    """
    timing = can.BitTimingFd.from_sample_point(
        f_clock=80_000_000,
        nom_bitrate=250_000,
        nom_sample_point=80.0,
        data_bitrate=1_212_121,
        data_sample_point=75.0,
    )
    assert timing.f_clock / (timing.nbt * timing.nom_brp) == 250_000

    args = {
        "f_clock": 20_000_000,
        "nom_bitrate": 125_000,
        "nom_sample_point": 75.0,
        "data_bitrate": 1_000_000,
        "data_sample_point": 75.0,
    }
    timing = can.BitTimingFd.from_sample_point(**args)
    assert timing.nom_brp == timing.data_brp

    def sample_point_deviation(t: can.BitTimingFd) -> float:
        return abs(t.nom_sample_point - 75.0) + abs(t.data_sample_point - 75.0)

    assert any(
        c.nom_brp != c.data_brp
        and c.nom_bitrate == 125_000
        and c.data_bitrate == 1_000_000
        and sample_point_deviation(c) < sample_point_deviation(timing)
        for c in can.BitTimingFd.iterate_from_sample_point(**args)
    )

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

    timing = can.BitTiming.from_bitrate_and_segments(
        f_clock=8_000_000, bitrate=500_000, tseg1=13, tseg2=2, sjw=1
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

    timing = can.BitTiming.from_bitrate_and_segments(
        f_clock=8_000_000, bitrate=1_000_000, tseg1=5, tseg2=2, sjw=1, strict=True
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

    assert timing.f_clock == 80_000_000
    assert timing.nom_bitrate == 500_000
    assert timing.nom_brp == 1
    assert timing.nbt == 160
    assert timing.nom_tseg1 == 119
    assert timing.nom_tseg2 == 40
    assert timing.nom_sjw == 40
    assert timing.nom_sample_point == 75
    assert timing.f_clock == 80_000_000
    assert timing.data_bitrate == 2_000_000
    assert timing.data_brp == 1
    assert timing.dbt == 40
    assert timing.data_tseg1 == 29
    assert timing.data_tseg2 == 10
    assert timing.data_sjw == 10
    assert timing.data_sample_point == 75

    # test strict invalid
    with pytest.raises(ValueError):
        can.BitTimingFd.from_bitrate_and_segments(
            f_clock=80_000_000,
            nom_bitrate=500_000,
            nom_tseg1=119,
            nom_tseg2=40,
            nom_sjw=40,
            data_bitrate=2_000_000,
            data_tseg1=29,
            data_tseg2=10,
            data_sjw=10,
            strict=True,
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

    # test strict invalid
    with pytest.raises(ValueError):
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
            strict=True,
        )

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


def test_from_btr():
    timing = can.BitTiming.from_registers(f_clock=8_000_000, btr0=0x00, btr1=0x14)
    assert timing.bitrate == 1_000_000
    assert timing.brp == 1
    assert timing.nbt == 8
    assert timing.tseg1 == 5
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.sample_point == 75
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x14


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

    # check that there is a solution for every sample point
    for sp in range(50, 100):
        can.BitTiming.from_sample_point(
            f_clock=16_000_000, bitrate=500_000, sample_point=sp
        )

    # check that there is a solution for every sample point
    for nsp in range(50, 100):
        for dsp in range(50, 100):
            can.BitTimingFd.from_sample_point(
                f_clock=80_000_000,
                nom_bitrate=500_000,
                nom_sample_point=nsp,
                data_bitrate=2_000_000,
                data_sample_point=dsp,
            )


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

    for nsp in range(50, 100):
        for dsp in range(50, 100):
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


def test_mapping():
    timing = can.BitTiming(f_clock=8_000_000, brp=1, tseg1=5, tseg2=2, sjw=1)
    timing_dict = dict(timing)
    assert timing_dict["f_clock"] == timing["f_clock"]
    assert timing_dict["brp"] == timing["brp"]
    assert timing_dict["tseg1"] == timing["tseg1"]
    assert timing_dict["tseg2"] == timing["tseg2"]
    assert timing_dict["sjw"] == timing["sjw"]
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
    assert fd_timing_dict["f_clock"] == fd_timing["f_clock"]
    assert fd_timing_dict["nom_brp"] == fd_timing["nom_brp"]
    assert fd_timing_dict["nom_tseg1"] == fd_timing["nom_tseg1"]
    assert fd_timing_dict["nom_tseg2"] == fd_timing["nom_tseg2"]
    assert fd_timing_dict["nom_sjw"] == fd_timing["nom_sjw"]
    assert fd_timing_dict["data_brp"] == fd_timing["data_brp"]
    assert fd_timing_dict["data_tseg1"] == fd_timing["data_tseg1"]
    assert fd_timing_dict["data_tseg2"] == fd_timing["data_tseg2"]
    assert fd_timing_dict["data_sjw"] == fd_timing["data_sjw"]
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

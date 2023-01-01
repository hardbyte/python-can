#!/usr/bin/env python
import pytest

import can


def test_sja1000():
    """Test some values obtained using other bit timing calculators."""
    timing = can.BitTiming(
        f_clock=8000000, bitrate=125000, tseg1=11, tseg2=4, sjw=2, nof_samples=3
    )
    assert timing.f_clock == 8000000
    assert timing.bitrate == 125000
    assert timing.brp == 4
    assert timing.nbt == 16
    assert timing.tseg1 == 11
    assert timing.tseg2 == 4
    assert timing.sjw == 2
    assert timing.nof_samples == 3
    assert timing.sample_point == 75
    assert timing.btr0 == 0x43
    assert timing.btr1 == 0xBA

    timing = can.BitTiming(f_clock=8000000, bitrate=500000, tseg1=13, tseg2=2, sjw=1)
    assert timing.f_clock == 8000000
    assert timing.bitrate == 500000
    assert timing.brp == 1
    assert timing.nbt == 16
    assert timing.tseg1 == 13
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.nof_samples == 1
    assert timing.sample_point == 87.5
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x1C

    timing = can.BitTiming(f_clock=8000000, bitrate=1000000, tseg1=5, tseg2=2, sjw=1)
    assert timing.f_clock == 8000000
    assert timing.bitrate == 1000000
    assert timing.brp == 1
    assert timing.nbt == 8
    assert timing.tseg1 == 5
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.nof_samples == 1
    assert timing.sample_point == 75
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x14


def test_can_fd():
    timing = can.BitTimingFd(
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



import struct
from can.interfaces.pcan.pcan import PCAN_BITRATES

def test_btr_persistence():
    f_clock = 8_000_000
    for btr0btr1 in PCAN_BITRATES.values():
        btr1, btr0 = struct.unpack("BB", btr0btr1)

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


def test_equality():
    t1 = can.BitTiming.from_registers(f_clock=8_000_000, btr0=0x00, btr1=0x14)
    t2 = can.BitTiming(
        f_clock=8_000_000, bitrate=1_000_000, tseg1=5, tseg2=2, sjw=1, nof_samples=1
    )
    t3 = can.BitTiming(
        f_clock=16_000_000, bitrate=1_000_000, tseg1=5, tseg2=2, sjw=1, nof_samples=1
    )
    assert t1 == t2
    assert t1 != t3
    assert t2 != t3
    assert t1 != 10

    t4 = can.BitTimingFd(
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
    t5 = can.BitTimingFd(
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
    timing = can.BitTiming(f_clock=8000000, bitrate=1000000, tseg1=5, tseg2=2, sjw=1)
    assert str(timing) == (
        "BR 1000000 bit/s, SP: 75.00%, BRP: 1, TSEG1: 5, TSEG2: 2, SJW: 1, "
        "BTR: 0014h, f_clock: 8MHz"
    )

    fd_timing = can.BitTimingFd(
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
    assert str(fd_timing) == (
        "NBR: 500000 bit/s, NSP: 75.00%, NBRP: 1, NTSEG1: 119, NTSEG2: 40, NSJW: 40, "
        "DBR: 2000000 bit/s, DSP: 75.00%, DBRP: 1, DTSEG1: 29, DTSEG2: 10, DSJW: 10, "
        "f_clock: 80MHz"
    )


def test_repr():
    timing = can.BitTiming(f_clock=8000000, bitrate=1000000, tseg1=5, tseg2=2, sjw=1)
    assert repr(timing) == (
        "can.BitTiming(f_clock=8000000, bitrate=1000000, tseg1=5, tseg2=2, sjw=1, nof_samples=1)"
    )

    fd_timing = can.BitTimingFd(
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
    assert repr(fd_timing) == (
        "can.BitTimingFd(f_clock=80000000, nom_bitrate=500000, nom_tseg1=119, nom_tseg2=40, "
        "nom_sjw=40, data_bitrate=2000000, data_tseg1=29, data_tseg2=10, data_sjw=10)"
    )


def test_mapping():
    timing = can.BitTiming(
        f_clock=8_000_000, bitrate=1_000_000, tseg1=5, tseg2=2, sjw=1
    )
    timing_dict = dict(timing)
    assert timing_dict["f_clock"] == timing["f_clock"]
    assert timing_dict["bitrate"] == timing["bitrate"]
    assert timing_dict["tseg1"] == timing["tseg1"]
    assert timing_dict["tseg2"] == timing["tseg2"]
    assert timing_dict["sjw"] == timing["sjw"]
    assert timing == can.BitTiming(**timing_dict)

    fd_timing = can.BitTimingFd(
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
    fd_timing_dict = dict(fd_timing)
    assert fd_timing_dict["f_clock"] == fd_timing["f_clock"]
    assert fd_timing_dict["nom_bitrate"] == fd_timing["nom_bitrate"]
    assert fd_timing_dict["nom_tseg1"] == fd_timing["nom_tseg1"]
    assert fd_timing_dict["nom_tseg2"] == fd_timing["nom_tseg2"]
    assert fd_timing_dict["nom_sjw"] == fd_timing["nom_sjw"]
    assert fd_timing_dict["data_bitrate"] == fd_timing["data_bitrate"]
    assert fd_timing_dict["data_tseg1"] == fd_timing["data_tseg1"]
    assert fd_timing_dict["data_tseg2"] == fd_timing["data_tseg2"]
    assert fd_timing_dict["data_sjw"] == fd_timing["data_sjw"]
    assert fd_timing == can.BitTimingFd(**fd_timing_dict)


def test_oscillator_tolerance():
    timing = can.BitTiming(
        f_clock=16_000_000, bitrate=500_000, tseg1=10, tseg2=5, sjw=4
    )
    osc_tol = timing.oscillator_tolerance(
        node_loop_delay_ns=250,
        bus_length_m=10.0,
    )
    assert osc_tol == pytest.approx(1.23, abs=1e-2)

    fd_timing = can.BitTimingFd(
        f_clock=80_000_000,
        nom_bitrate=500_000,
        nom_tseg1=27,
        nom_tseg2=4,
        nom_sjw=4,
        data_bitrate=2_000_000,
        data_tseg1=6,
        data_tseg2=1,
        data_sjw=1,
    )
    osc_tol = fd_timing.oscillator_tolerance(
        node_loop_delay_ns=250,
        bus_length_m=10.0,
    )
    assert osc_tol == pytest.approx(0.48543689320388345, abs=1e-2)

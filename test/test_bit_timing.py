#!/usr/bin/env python

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
        "BTR: 0014h, f_clock: 8MHz, df_clock: 0.62%"
    )

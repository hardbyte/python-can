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
    timing = can.BitTiming(
        f_clock=80000000, bitrate=500000, tseg1=119, tseg2=40, sjw=40
    )
    assert timing.f_clock == 80000000
    assert timing.bitrate == 500000
    assert timing.brp == 1
    assert timing.nbt == 160
    assert timing.tseg1 == 119
    assert timing.tseg2 == 40
    assert timing.sjw == 40
    assert timing.sample_point == 75

    timing = can.BitTiming(
        f_clock=80000000, bitrate=2000000, tseg1=29, tseg2=10, sjw=10
    )
    assert timing.f_clock == 80000000
    assert timing.bitrate == 2000000
    assert timing.brp == 1
    assert timing.nbt == 40
    assert timing.tseg1 == 29
    assert timing.tseg2 == 10
    assert timing.sjw == 10
    assert timing.sample_point == 75


def test_from_btr():
    timing = can.BitTiming(f_clock=8000000, btr0=0x00, btr1=0x14)
    assert timing.bitrate == 1000000
    assert timing.brp == 1
    assert timing.nbt == 8
    assert timing.tseg1 == 5
    assert timing.tseg2 == 2
    assert timing.sjw == 1
    assert timing.sample_point == 75
    assert timing.btr0 == 0x00
    assert timing.btr1 == 0x14


def test_string_representation():
    timing = can.BitTiming(f_clock=8000000, bitrate=1000000, tseg1=5, tseg2=2, sjw=1)
    assert (
        str(timing)
        == "1000000 bits/s, sample point: 75.00%, BRP: 1, TSEG1: 5, TSEG2: 2, SJW: 1, BTR: 0014h"
    )

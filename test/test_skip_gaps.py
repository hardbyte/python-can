"""Deterministic playback schedules, without real sleeps or CAN hardware."""

from unittest.mock import MagicMock, patch

import pytest

import can
import can.player


class Clock:
    def __init__(self):
        self.now = 100.0

    def perf_counter(self):
        return self.now

    def sleep(self, delay):
        assert delay > 0
        self.now += delay


@pytest.mark.parametrize("remove", [False, True])
@pytest.mark.parametrize(
    "timestamps,skip,capped,removed",
    [
        ([0, 0.25, 5.25, 5.5], 1, [0, 0.25, 1.25, 1.5], [0, 0.25, 0.25, 0.5]),
        ([0, 1, 2], 1, [0, 1, 2], [0, 1, 2]),
        ([0, 5, 10, 10.25], 1, [0, 1, 2, 2.25], [0, 0, 0, 0.25]),
        ([0, 0, -1, 0.25], 1, [0, 0, 0, 0.25], [0, 0, 0, 0.25]),
        ([0, 0.25, 5.25, 5.5], 0, [0, 0.25, 5.25, 5.5], [0, 0.25, 5.25, 5.5]),
    ],
)
def test_recorded_schedule(remove, timestamps, skip, capped, removed):
    clock = Clock()
    messages = [
        can.Message(timestamp=t, arbitration_id=i) for i, t in enumerate(timestamps)
    ]
    options = {"skip_gaps": True} if remove else {}
    observed = []
    collected = []
    with (
        patch("can.io.player.time.perf_counter", clock.perf_counter),
        patch("can.io.player.time.sleep", clock.sleep),
    ):
        for message in can.MessageSync(iter(messages), skip=skip, **options):
            observed.append(round(clock.now - 100, 6))
            collected.append(message)
    assert observed == (removed if remove else capped)
    assert len(collected) == len(messages)
    assert all(a is b for a, b in zip(collected, messages))


@pytest.mark.parametrize("remove", [False, True])
@pytest.mark.parametrize("gap,expected", [(0.25, [0.25, 0.5]), (2, [1, 2])])
def test_fixed_gap_unchanged(remove, gap, expected):
    clock = Clock()
    options = {"skip_gaps": True} if remove else {}
    observed = []
    with (
        patch("can.io.player.time.perf_counter", clock.perf_counter),
        patch("can.io.player.time.sleep", clock.sleep),
    ):
        for _ in can.MessageSync(
            [can.Message(), can.Message()],
            timestamps=False,
            gap=gap,
            skip=1,
            **options,
        ):
            observed.append(clock.now - 100)
    assert observed == expected


@pytest.mark.parametrize("remove", [False, True])
@pytest.mark.parametrize("loops", [1, 2])
def test_player_cli(remove, loops):
    clock = Clock()
    bus = MagicMock()
    observed = []
    bus.send.side_effect = lambda message: observed.append(
        (round(clock.now - 100, 6), message.arbitration_id)
    )
    argv = [
        "can_player",
        "--sk",
        "1",
        "--loop",
        str(loops),
        "test/data/test_CanMessage.asc",
    ]
    if remove:
        argv.insert(1, "--remove-gaps")
    with (
        patch("sys.argv", argv),
        patch("can.player.create_bus_from_namespace") as create_bus,
        patch("can.io.player.time.perf_counter", clock.perf_counter),
        patch("can.io.player.time.sleep", clock.sleep),
    ):
        create_bus.return_value.__enter__.return_value = bus
        can.player.main()
    expected = []
    for iteration in range(loops):
        expected.extend(
            [
                (0 if remove else iteration, 0xC8),
                (0 if remove else iteration + 1, 0x6F9),
            ]
        )
    assert observed == expected
    create_bus.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize(
    "remove,expected", [(False, [0, 3, 3.25]), (True, [0, 2, 2.25])]
)
def test_processing_time_counts_towards_wait(remove, expected):
    clock = Clock()
    messages = [can.Message(timestamp=t) for t in [0, 5, 5.25]]
    options = {"skip_gaps": True} if remove else {}
    observed = []
    with (
        patch("can.io.player.time.perf_counter", clock.perf_counter),
        patch("can.io.player.time.sleep", clock.sleep),
    ):
        for index, _ in enumerate(can.MessageSync(messages, skip=1, **options)):
            observed.append(clock.now - 100)
            if index == 0:
                clock.now += 2
    assert observed == expected

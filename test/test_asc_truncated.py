"""Regressions for ASC records cut off during logging (#2160)."""

from io import StringIO

import pytest

import can

HEADER = "base hex timestamps relative\ninternal events logged\n"
GOOD = "0.100000 1 123 Rx d 2 01 02"


@pytest.mark.parametrize(
    "broken",
    [
        "0.100000 1 1d3 Rx d 8 01 02",
        "0.100000 1 1d3 Rx d 8",
        "0.100000 CANFD 1 Rx 1d3 1 0 8 8",
        "0.100000 CANFD 1 Rx 1d3 1 0 8 8 01 02",
        "0.100000 CANFD 1 Rx 1d3 FrameName 1 0 8 8 01 02",
    ],
)
def test_truncated_frame_is_reported_and_following_frame_survives(broken, caplog):
    with can.ASCReader(
        StringIO(HEADER + GOOD + "\n" + broken + "\n" + GOOD + "\n"),
        relative_timestamp=False,
    ) as reader:
        messages = list(reader)
    assert len(messages) == 2
    assert [bytes(msg.data) for msg in messages] == [b"\x01\x02", b"\x01\x02"]
    assert messages[-1].timestamp == pytest.approx(0.3)
    assert len(caplog.records) == 1
    assert broken in caplog.records[0].message


@pytest.mark.parametrize(
    "frame,length,remote",
    [
        ("0.100000 1 123 Rx d 0", 0, False),
        ("0.100000 1 123 Rx r 8", 8, True),
        ("0.100000 CANFD 1 Rx 123 1 0 2 2 01 02 0 0 1000", 2, False),
        ("0.100000 CANFD 1 Rx 123 0 0 8 0 0 0 10", 8, True),
    ],
)
def test_complete_empty_and_remote_records_are_unchanged(frame, length, remote, caplog):
    with can.ASCReader(StringIO(HEADER + frame + "\n")) as reader:
        (message,) = reader
    assert message.dlc == length
    assert message.is_remote_frame == remote
    assert not caplog.records

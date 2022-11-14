#!/usr/bin/env python

import unittest
import sys
from math import isinf, isnan
from copy import copy, deepcopy
import pickle
from datetime import timedelta

from hypothesis import HealthCheck, given, settings
import hypothesis.errors
import hypothesis.strategies as st

from can import Message

from .message_helper import ComparingMessagesTestCase
from .config import IS_GITHUB_ACTIONS, IS_WINDOWS, IS_PYPY

import pytest


class TestMessageClass(unittest.TestCase):
    """
    This test tries many inputs to the message class constructor and then sanity checks
    all methods and ensures that nothing crashes. It also checks whether Message._check()
    allows all valid can frames.
    """

    @given(
        timestamp=st.floats(min_value=0.0),
        arbitration_id=st.integers(),
        is_extended_id=st.booleans(),
        is_remote_frame=st.booleans(),
        is_error_frame=st.booleans(),
        channel=st.one_of(st.text(), st.integers()),
        dlc=st.integers(min_value=0, max_value=8),
        data=st.one_of(st.binary(min_size=0, max_size=8), st.none()),
        is_fd=st.booleans(),
        bitrate_switch=st.booleans(),
        error_state_indicator=st.booleans(),
    )
    # The first run may take a second on CI runners and will hit the deadline
    @settings(
        max_examples=2000,
        suppress_health_check=[HealthCheck.too_slow],
        deadline=None if IS_GITHUB_ACTIONS else timedelta(milliseconds=500),
    )
    @pytest.mark.xfail(
        IS_WINDOWS and IS_PYPY,
        raises=hypothesis.errors.Flaky,
        reason="Hypothesis generates inconsistent timestamp floats on Windows+PyPy-3.7",
    )
    def test_methods(self, **kwargs):
        is_valid = not (
            (
                not kwargs["is_remote_frame"]
                and (len(kwargs["data"] or []) != kwargs["dlc"])
            )
            or (kwargs["arbitration_id"] >= 0x800 and not kwargs["is_extended_id"])
            or kwargs["arbitration_id"] >= 0x20000000
            or kwargs["arbitration_id"] < 0
            or (
                kwargs["is_remote_frame"]
                and (kwargs["is_fd"] or kwargs["is_error_frame"])
            )
            or (kwargs["is_remote_frame"] and len(kwargs["data"] or []) > 0)
            or (
                (kwargs["bitrate_switch"] or kwargs["error_state_indicator"])
                and not kwargs["is_fd"]
            )
            or isnan(kwargs["timestamp"])
            or isinf(kwargs["timestamp"])
        )

        # this should return normally and not throw an exception
        message = Message(check=is_valid, **kwargs)

        if kwargs["data"] is None or kwargs["is_remote_frame"]:
            kwargs["data"] = bytearray()

        if not is_valid and not kwargs["is_remote_frame"]:
            with self.assertRaises(ValueError):
                Message(check=True, **kwargs)

        self.assertGreater(len(str(message)), 0)
        self.assertGreater(len(message.__repr__()), 0)
        if is_valid:
            self.assertEqual(len(message), kwargs["dlc"])
        self.assertTrue(bool(message))
        self.assertGreater(len("{}".format(message)), 0)
        _ = "{}".format(message)
        with self.assertRaises(Exception):
            _ = "{somespec}".format(
                message
            )  # pylint: disable=missing-format-argument-key
        if sys.version_info.major > 2:
            self.assertEqual(bytearray(bytes(message)), kwargs["data"])

        # check copies and equalities
        if is_valid:
            self.assertEqual(message, message)
            normal_copy = copy(message)
            deep_copy = deepcopy(message)
            for other in (normal_copy, deep_copy, message):
                self.assertTrue(message.equals(other, timestamp_delta=None))
                self.assertTrue(message.equals(other))
                self.assertTrue(message.equals(other, timestamp_delta=0))


class MessageSerialization(unittest.TestCase, ComparingMessagesTestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        ComparingMessagesTestCase.__init__(
            self, allowed_timestamp_delta=0.016, preserves_channel=True
        )

    def test_serialization(self):
        message = Message(
            timestamp=1.0,
            arbitration_id=0x401,
            is_extended_id=False,
            is_remote_frame=False,
            is_error_frame=False,
            channel=1,
            dlc=6,
            data=bytearray([0x01, 0x02, 0x03, 0x04, 0x05, 0x06]),
            is_fd=False,
        )

        serialized = pickle.dumps(message, -1)
        deserialized = pickle.loads(serialized)

        self.assertMessageEqual(message, deserialized)


if __name__ == "__main__":
    unittest.main()

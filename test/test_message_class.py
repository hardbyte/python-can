#!/usr/bin/env python
# coding: utf-8

import unittest
import sys
from math import isinf, isnan
from copy import copy, deepcopy

from hypothesis import given, settings, reproduce_failure
import hypothesis.strategies as st

from can import Message


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
        error_state_indicator=st.booleans()
    )
    @settings(max_examples=2000)
    def test_methods(self, **kwargs):
        is_valid = not (
            (not kwargs['is_remote_frame'] and (len(kwargs['data'] or []) != kwargs['dlc'])) or
            (kwargs['arbitration_id'] >= 0x800 and not kwargs['is_extended_id']) or
            kwargs['arbitration_id'] >= 0x20000000 or
            kwargs['arbitration_id'] < 0 or
            (kwargs['is_remote_frame'] and kwargs['is_error_frame']) or
            (kwargs['is_remote_frame'] and len(kwargs['data'] or []) > 0) or
            ((kwargs['bitrate_switch'] or kwargs['error_state_indicator']) and not kwargs['is_fd']) or
            isnan(kwargs['timestamp']) or
            isinf(kwargs['timestamp'])
        )

        # this should return normally and not throw an exception
        message = Message(check=is_valid, **kwargs)

        if kwargs['data'] is None or kwargs['is_remote_frame']:
            kwargs['data'] = bytearray()

        if not is_valid and not kwargs['is_remote_frame']:
            with self.assertRaises(ValueError):
                Message(check=True, **kwargs)

        self.assertGreater(len(str(message)), 0)
        self.assertGreater(len(message.__repr__()), 0)
        if is_valid:
            self.assertEqual(len(message), kwargs['dlc'])
        self.assertTrue(bool(message))
        self.assertGreater(len("{}".format(message)), 0)
        _ = "{}".format(message)
        with self.assertRaises(Exception):
            _ = "{somespec}".format(message)
        if sys.version_info.major > 2:
            self.assertEqual(bytearray(bytes(message)), kwargs['data'])

        # check copies and equalities
        if is_valid:
            self.assertEqual(message, message)        
            normal_copy = copy(message)
            deep_copy = deepcopy(message)
            for other in (normal_copy, deep_copy, message):
                self.assertTrue(message.equals(other, timestamp_delta=None))
                self.assertTrue(message.equals(other))
                self.assertTrue(message.equals(other, timestamp_delta=0))


if __name__ == '__main__':
    unittest.main()

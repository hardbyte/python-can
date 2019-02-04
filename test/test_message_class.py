#!/usr/bin/env python
# coding: utf-8

import unittest
import sys
from math import isinf, isnan
from copy import copy, deepcopy

from hypothesis import given, settings
import hypothesis.strategies as st

from can import Message


class TestMessageClass(unittest.TestCase):

    @given(
        timestamp=st.floats(min_value=0.0),
        arbitration_id=st.integers(min_value=0, max_value=0x20000000-1),
        is_extended_id=st.booleans(),
        is_remote_frame=st.booleans(),
        is_error_frame=st.booleans(),
        channel=st.one_of(st.characters(), st.integers()),
        dlc=st.integers(min_value=0, max_value=8),
        data=st.binary(min_size=0, max_size=8),
        is_fd=st.booleans(),
        bitrate_switch=st.booleans(),
        error_state_indicator=st.booleans()
    )
    @settings(max_examples=1000, deadline=10)
    def test_methods(self, **kwargs):
        is_valid = not (
            len(kwargs['data']) != kwargs['dlc'] or
            (kwargs['arbitration_id'] >= 0x800 and not kwargs['is_extended_id']) or
            (kwargs['is_remote_frame'] and kwargs['is_error_frame']) or
            ((kwargs['bitrate_switch'] or kwargs['error_state_indicator']) and not kwargs['is_fd']),
            isnan(kwargs['timestamp']) or
            isinf(kwargs['timestamp'])
        )

        message = Message(check=is_valid, **kwargs)
        self.assertGreater(len(str(message)), 0)
        self.assertGreater(len(message.__repr__()), 0)
        if is_valid:
            self.assertEqual(len(message), kwargs['dlc'])
        self.assertTrue(bool(message))
        self.assertGreater(len("{}".format(message)), 0)
        with self.assertRaises(Exception):
            _ = "{some_spec}".format(message)
        if sys.version_info.major > 2:
            self.assertEqual(bytes(message), kwargs['data'])

        # check copies and equalities
        if is_valid:
            self.assertEqual(message, message)        
            normal_copy = copy(message)
            deep_copy = deepcopy(message)
            for other in (normal_copy, deep_copy, message):
                self.assertTrue(message.equals(other), str(other))


if __name__ == '__main__':
    unittest.main()

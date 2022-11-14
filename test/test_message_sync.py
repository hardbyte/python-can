#!/usr/bin/env python

"""
This module tests :class:`can.MessageSync`.
"""

from copy import copy
import time
import gc

import unittest
import pytest

from can import MessageSync, Message

from .config import IS_CI, IS_TRAVIS, IS_OSX, IS_GITHUB_ACTIONS, IS_LINUX
from .message_helper import ComparingMessagesTestCase
from .data.example_data import TEST_MESSAGES_BASE


TEST_FEWER_MESSAGES = TEST_MESSAGES_BASE[::2]


def inc(value):
    """Makes the test boundaries give some more space when run on the CI server."""
    if IS_CI:
        return value * 1.5
    else:
        return value


skip_on_unreliable_platforms = unittest.skipIf(
    (IS_TRAVIS and IS_OSX) or (IS_GITHUB_ACTIONS and not IS_LINUX),
    "this environment's timings are too unpredictable",
)


@skip_on_unreliable_platforms
class TestMessageSync(unittest.TestCase, ComparingMessagesTestCase):
    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        ComparingMessagesTestCase.__init__(self)

    def setup_method(self, _):
        # disabling the garbage collector makes the time readings more reliable
        gc.disable()

    def teardown_method(self, _):
        # we need to reenable the garbage collector again
        gc.enable()

    def test_general(self):
        messages = [
            Message(timestamp=50.0),
            Message(timestamp=50.0),
            Message(timestamp=50.0 + 0.05),
            Message(timestamp=50.0 + 0.13),
            Message(timestamp=50.0),  # back in time
        ]
        sync = MessageSync(messages, gap=0.0, skip=0.0)

        t_start = time.perf_counter()
        collected = []
        timings = []
        for message in sync:
            t_now = time.perf_counter()
            collected.append(message)
            timings.append(t_now - t_start)

        self.assertMessagesEqual(messages, collected)
        self.assertEqual(len(timings), len(messages), "programming error in test code")

        self.assertTrue(0.0 <= timings[0] < 0.0 + inc(0.02), str(timings[0]))
        self.assertTrue(0.0 <= timings[1] < 0.0 + inc(0.02), str(timings[1]))
        self.assertTrue(0.045 <= timings[2] < 0.05 + inc(0.02), str(timings[2]))
        self.assertTrue(0.125 <= timings[3] < 0.13 + inc(0.02), str(timings[3]))
        self.assertTrue(0.125 <= timings[4] < 0.13 + inc(0.02), str(timings[4]))

    def test_skip(self):
        messages = copy(TEST_FEWER_MESSAGES)
        sync = MessageSync(messages, skip=0.005, gap=0.0)

        before = time.perf_counter()
        collected = list(sync)
        after = time.perf_counter()
        took = after - before

        # the handling of the messages itself also takes some time:
        # ~0.001 s/message on a ThinkPad T560 laptop (Ubuntu 18.04, i5-6200U)
        assert 0 < took < inc(len(messages) * (0.005 + 0.003)), "took: {}s".format(took)

        self.assertMessagesEqual(messages, collected)


@skip_on_unreliable_platforms
@pytest.mark.parametrize(
    "timestamp_1,timestamp_2", [(0.0, 0.0), (0.0, 0.01), (0.01, 1.5)]
)
def test_gap(timestamp_1, timestamp_2):
    """This method is alone so it can be parameterized."""
    messages = [
        Message(arbitration_id=0x1, timestamp=timestamp_1),
        Message(arbitration_id=0x2, timestamp=timestamp_2),
    ]
    sync = MessageSync(messages, timestamps=False, gap=0.1)

    gc.disable()
    before = time.perf_counter()
    collected = list(sync)
    after = time.perf_counter()
    gc.enable()
    took = after - before

    assert 0.195 <= took < 0.2 + inc(0.02)
    assert messages == collected


if __name__ == "__main__":
    unittest.main()

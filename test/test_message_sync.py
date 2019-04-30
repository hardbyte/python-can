#!/usr/bin/env python
# coding: utf-8

"""
This module tests :class:`can.MessageSync`.
"""

from __future__ import absolute_import

from copy import copy
from time import time
import gc

import unittest
import pytest

from can import MessageSync, Message

from .config import IS_APPVEYOR
from .message_helper import ComparingMessagesTestCase
from .data.example_data import TEST_MESSAGES_BASE

TEST_FEWER_MESSAGES = TEST_MESSAGES_BASE[::2]


@unittest.skipIf(IS_APPVEYOR, "this environment's timings are too unpredictable")
class TestMessageFiltering(unittest.TestCase, ComparingMessagesTestCase):

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        ComparingMessagesTestCase.__init__(self)

    def setup_method(self, _):
        gc.disable()

    def teardown_method(self, _):
        gc.enable()

    @pytest.mark.timeout(0.2)
    def test_general(self):
        messages = [
            Message(timestamp=50.0),
            Message(timestamp=50.0),
            Message(timestamp=50.0 + 0.05),
            Message(timestamp=50.0 + 0.05 + 0.08),
            Message(timestamp=50.0) # back in time
        ]
        sync = MessageSync(messages, gap=0.0)

        start = time()
        collected = []
        timings = []
        for message in sync:
            collected.append(message)
            now = time()
            timings.append(now - start)
            start = now


        self.assertMessagesEqual(messages, collected)
        self.assertEqual(len(timings), len(messages), "programming error in test code")

        self.assertTrue(0.0 <= timings[0] < 0.005, str(timings[0]))
        self.assertTrue(0.0 <= timings[1] < 0.005, str(timings[1]))
        self.assertTrue(0.045 <= timings[2] < 0.055, str(timings[2]))
        self.assertTrue(0.075 <= timings[3] < 0.085, str(timings[3]))
        self.assertTrue(0.0 <= timings[4] < 0.005, str(timings[4]))

    @pytest.mark.timeout(0.1 * len(TEST_FEWER_MESSAGES)) # very conservative
    def test_skip(self):
        messages = copy(TEST_FEWER_MESSAGES)
        sync = MessageSync(messages, skip=0.005, gap=0.0)

        before = time()
        collected = list(sync)
        after = time()
        took = after - before

        # the handling of the messages itself also take time: ~0.001 s/msg on my laptop
        assert 0 < took < len(messages) * (0.005 + 0.003), "took: {}s".format(took)

        self.assertMessagesEqual(messages, collected)


@unittest.skipIf(IS_APPVEYOR, "this environment's timings are too unpredictable")
@pytest.mark.timeout(0.3)
@pytest.mark.parametrize("timestamp_1,timestamp_2", [
    (0.0, 0.0),
    (0.0, 0.01),
    (0.01, 0.0),
])
def test_gap(timestamp_1, timestamp_2):
    """This method is alone so it can be parameterized."""
    messages = [
        Message(arbitration_id=0x1, timestamp=timestamp_1),
        Message(arbitration_id=0x2, timestamp=timestamp_2)
    ]
    sync = MessageSync(messages, gap=0.1)

    gc.disable()
    before = time()
    collected = list(sync)
    after = time()
    gc.enable()
    took = after - before

    assert 0.1 <= took < 0.3
    assert messages == collected


if __name__ == '__main__':
    unittest.main()

#!/usr/bin/env python

"""
This module tests :meth:`can.BusABC._matches_filters`.
"""

import unittest
from unittest.mock import MagicMock, patch

from can import Bus, Message

from .data.example_data import TEST_ALL_MESSAGES

EXAMPLE_MSG = Message(arbitration_id=0x123, is_extended_id=True)
HIGHEST_MSG = Message(arbitration_id=0x1FFFFFFF, is_extended_id=True)

MATCH_EXAMPLE = [{"can_id": 0x123, "can_mask": 0x1FFFFFFF, "extended": True}]

MATCH_ONLY_HIGHEST = [{"can_id": 0xFFFFFFFF, "can_mask": 0x1FFFFFFF, "extended": True}]


class TestMessageFiltering(unittest.TestCase):
    def setUp(self):
        self.bus = Bus(interface="virtual", channel="testy")

    def tearDown(self):
        self.bus.shutdown()

    def test_match_all(self):
        # explicitly
        self.bus.set_filters()
        self.assertTrue(self.bus._matches_filters(EXAMPLE_MSG))
        # implicitly
        self.bus.set_filters(None)
        self.assertTrue(self.bus._matches_filters(EXAMPLE_MSG))

    def test_match_filters_is_empty(self):
        self.bus.set_filters([])
        for msg in TEST_ALL_MESSAGES:
            self.assertTrue(self.bus._matches_filters(msg))

    def test_match_example_message(self):
        self.bus.set_filters(MATCH_EXAMPLE)
        self.assertTrue(self.bus._matches_filters(EXAMPLE_MSG))
        self.assertFalse(self.bus._matches_filters(HIGHEST_MSG))
        self.bus.set_filters(MATCH_ONLY_HIGHEST)
        self.assertFalse(self.bus._matches_filters(EXAMPLE_MSG))
        self.assertTrue(self.bus._matches_filters(HIGHEST_MSG))

    def test_empty_queue_up_to_match(self):
        bus2 = Bus(interface="virtual", channel="testy")
        self.bus.set_filters(MATCH_EXAMPLE)
        bus2.send(HIGHEST_MSG)
        bus2.send(EXAMPLE_MSG)
        actual = self.bus.recv(timeout=0)
        bus2.shutdown()
        self.assertTrue(
            EXAMPLE_MSG.equals(
                actual, timestamp_delta=None, check_direction=False, check_channel=False
            )
        )


@patch("can.bus.time")
class TestMessageFilterRetryTiming(unittest.TestCase):
    def setUp(self):
        self.bus = Bus(interface="virtual", channel="testy")
        self.bus._recv_internal = MagicMock(name="_recv_internal")

    def tearDown(self):
        self.bus.shutdown()

    def test_propagate_recv_internal_timeout(self, time: MagicMock) -> None:
        self.bus._recv_internal.side_effect = [
            (None, False),
        ]
        time.side_effect = [0]
        self.bus.set_filters(MATCH_EXAMPLE)
        self.assertIsNone(self.bus.recv(timeout=3))

    def test_retry_with_adjusted_timeout(self, time: MagicMock) -> None:
        self.bus._recv_internal.side_effect = [
            (HIGHEST_MSG, False),
            (EXAMPLE_MSG, False),
        ]
        time.side_effect = [0, 1]
        self.bus.set_filters(MATCH_EXAMPLE)
        self.bus.recv(timeout=3)
        self.bus._recv_internal.assert_called_with(timeout=2)

    def test_keep_timeout_non_negative(self, time: MagicMock) -> None:
        self.bus._recv_internal.side_effect = [
            (HIGHEST_MSG, False),
            (EXAMPLE_MSG, False),
        ]
        time.side_effect = [0, 1]
        self.bus.set_filters(MATCH_EXAMPLE)
        self.bus.recv(timeout=0.5)
        self.bus._recv_internal.assert_called_with(timeout=0)


if __name__ == "__main__":
    unittest.main()

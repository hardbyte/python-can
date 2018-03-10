#!/usr/bin/env python
# coding: utf-8

"""
This module tests :meth:`can.BusABC._matches_filters`.
"""

from __future__ import absolute_import

import unittest

from can import Bus, Message

from .data.example_data import TEST_ALL_MESSAGES


EXAMPLE_MSG = Message(arbitration_id=123, extended_id=True)

MATCH_EXAMPLE = [{
    "can_id": 123,
    "can_mask": 0x1FFFFFFF,
    "extended": True
}]

MATCH_ONLY_HIGHEST = [{
    "can_id": 0xFFFFFFFF,
    "can_mask": 0x1FFFFFFF,
    "extended": True
}]


class TestMessageFiltering(unittest.TestCase):

    def setUp(self):
        self.bus = can.Bus(bustype='virtual', channel='testy')

    def tearDown(self):
        self.bus.shutdown()

    def test_match_all(self):
        # explicitly
        self.bus.set_filters()
        self.assertTrue(self.bus._matches_filters(EXAMPLE_MSG))
        # implicitly
        self.bus.set_filters(None)
        self.assertTrue(self.bus._matches_filters(EXAMPLE_MSG))

    def test_match_nothing(self):
        self.bus.set_filters([])
        for msg in TEST_ALL_MESSAGES:
            self.assertFalse(self.bus._matches_filters(msg))

    def test_match_example_message(self):
        raise NotImplementedError("TODO")


if __name__ == '__main__':
    unittest.main()

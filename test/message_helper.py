#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, print_function

from copy import copy


class ComparingMessagesTestCase(object):
    """Must be extended by a class also extending a unittest.TestCase.
    """

    def __init__(self, allowed_timestamp_delta=0.0, preserves_channel=True):
        """
        :param float or int or None allowed_timestamp_delta: directly passed to :meth:`can.Message.equals`
        :param bool preserves_channel: if True, checks that the channel attribute is preserved
        """
        self.allowed_timestamp_delta = allowed_timestamp_delta
        self.preserves_channel = preserves_channel

    def assertMessageEqual(self, message_1, message_2):
        """
        Checks that two messages are equal, according to the given rules.
        """

        if message_1.equals(message_2, timestamp_delta=self.allowed_timestamp_delta):
            return
        elif self.preserves_channel:
            print("Comparing: message 1: {!r}".format(message_1))
            print("           message 2: {!r}".format(message_2))
            self.fail("messages are unequal with allowed timestamp delta {}".format(self.allowed_timestamp_delta))
        else:
            message_2 = copy(message_2) # make sure this method is pure
            message_2.channel = message_1.channel
            if message_1.equals(message_2, timestamp_delta=self.allowed_timestamp_delta):
                return
            else:
                print("Comparing: message 1: {!r}".format(message_1))
                print("           message 2: {!r}".format(message_2))
                self.fail("messages are unequal with allowed timestamp delta {} even when ignoring channels" \
                          .format(self.allowed_timestamp_delta))

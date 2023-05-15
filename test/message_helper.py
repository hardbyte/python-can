#!/usr/bin/env python

"""
This module contains a helper for writing test cases that need to compare messages.
"""


class ComparingMessagesTestCase:
    """
    Must be extended by a class also extending a unittest.TestCase.

    .. note:: This class does not extend unittest.TestCase so it does not get
              run as a test itself.
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

        if not message_1.equals(
            message_2,
            check_channel=self.preserves_channel,
            timestamp_delta=self.allowed_timestamp_delta,
        ):
            print(f"Comparing: message 1: {message_1!r}")
            print(f"           message 2: {message_2!r}")
            self.fail(f"messages are unequal: \n{message_1}\n{message_2}")

    def assertMessagesEqual(self, messages_1, messages_2):
        """
        Checks the order and content of the individual messages pairwise.
        Raises an error if the lengths of the sequences are not equal.
        """
        self.assertEqual(
            len(messages_1), len(messages_2), "the number of messages differs"
        )

        for message_1, message_2 in zip(messages_1, messages_2):
            self.assertMessageEqual(message_1, message_2)

#!/usr/bin/env python

"""
This module contains some example data, like messages of different
types and example comments with different challenges.
"""

import random
from operator import attrgetter

from can import Message

# make tests more reproducible
random.seed(13339115)


def sort_messages(messages):
    """
    Sorts the given messages by timestamps (ascending).

    :param Iterable[can.Message] messages: a sequence of messages to sort
    :rtype: list
    """
    return list(sorted(messages, key=attrgetter("timestamp")))


# some random number
TEST_TIME = 1483389946.197


# List of messages of different types that can be used in tests
TEST_MESSAGES_BASE = sort_messages(
    [
        Message(
            # empty
            timestamp=1e-4,
        ),
        Message(
            # only data
            timestamp=2e-4,
            data=[0x00, 0x42],
        ),
        Message(
            # no data
            timestamp=3e-4,
            arbitration_id=0xAB,
            is_extended_id=False,
        ),
        Message(
            # no data
            timestamp=4e-4,
            arbitration_id=0x42,
            is_extended_id=True,
        ),
        Message(
            # no data
            timestamp=5e-4,
            arbitration_id=0xABCDEF,
        ),
        Message(
            # empty data
            timestamp=6e-4,
            data=[],
        ),
        Message(
            # empty data
            timestamp=7e-4,
            data=[0xFF, 0xFE, 0xFD],
        ),
        Message(
            # with channel as integer
            timestamp=8e-4,
            channel=0,
        ),
        Message(
            # with channel as integer
            timestamp=9e-4,
            channel=42,
        ),
        Message(
            # with channel as string
            timestamp=10e-4,
            channel="vcan0",
        ),
        Message(
            # with channel as string
            timestamp=11e-4,
            channel="awesome_channel",
        ),
        Message(
            arbitration_id=0xABCDEF,
            is_extended_id=True,
            timestamp=TEST_TIME,
            data=[1, 2, 3, 4, 5, 6, 7, 8],
        ),
        Message(
            arbitration_id=0x123,
            is_extended_id=False,
            timestamp=TEST_TIME + 42.42,
            data=[0xFF, 0xFF],
        ),
        Message(
            arbitration_id=0xDADADA,
            is_extended_id=True,
            timestamp=TEST_TIME + 0.165,
            data=[1, 2, 3, 4, 5, 6, 7, 8],
        ),
        Message(
            arbitration_id=0x123,
            is_extended_id=False,
            timestamp=TEST_TIME + 0.365,
            data=[254, 255],
        ),
        Message(
            arbitration_id=0x768, is_extended_id=False, timestamp=TEST_TIME + 3.165
        ),
    ]
)


TEST_MESSAGES_CAN_FD = sort_messages(
    [
        Message(timestamp=12e-4, is_fd=True, data=range(64)),
        Message(timestamp=13e-4, is_fd=True, data=range(8)),
        Message(timestamp=14e-4, is_fd=True, data=range(8), bitrate_switch=True),
        Message(timestamp=15e-4, is_fd=True, data=range(8), error_state_indicator=True),
    ]
)


TEST_MESSAGES_REMOTE_FRAMES = sort_messages(
    [
        Message(
            arbitration_id=0xDADADA,
            is_extended_id=True,
            is_remote_frame=True,
            timestamp=TEST_TIME + 0.165,
        ),
        Message(
            arbitration_id=0x123,
            is_extended_id=False,
            is_remote_frame=True,
            timestamp=TEST_TIME + 0.365,
        ),
        Message(
            arbitration_id=0x768,
            is_extended_id=False,
            is_remote_frame=True,
            timestamp=TEST_TIME + 3.165,
        ),
        Message(
            arbitration_id=0xABCDEF,
            is_extended_id=True,
            is_remote_frame=True,
            timestamp=TEST_TIME + 7858.67,
        ),
    ]
)


TEST_MESSAGES_ERROR_FRAMES = sort_messages(
    [
        Message(is_error_frame=True),
        Message(is_error_frame=True, timestamp=TEST_TIME + 0.170),
        Message(is_error_frame=True, timestamp=TEST_TIME + 17.157),
    ]
)


TEST_ALL_MESSAGES = sort_messages(
    TEST_MESSAGES_BASE + TEST_MESSAGES_REMOTE_FRAMES + TEST_MESSAGES_ERROR_FRAMES
)


TEST_COMMENTS = [
    "This is the first comment",
    "",  # empty comment
    "This third comment contains some strange characters: 'ä\"§$%&/()=?__::_Öüßêè and ends here.",
    (
        "This fourth comment is quite long! "
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. "
        "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. "
        "Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi."
    ),
]


def generate_message(arbitration_id):
    """
    Generates a new message with the given ID, some random data
    and a non-extended ID.
    """
    data = bytearray([random.randrange(0, 2**8 - 1) for _ in range(8)])
    return Message(
        arbitration_id=arbitration_id,
        data=data,
        is_extended_id=False,
        timestamp=TEST_TIME,
    )

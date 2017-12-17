"""
This module contains some example data, like messages fo different
types and example comments with different challenges.
"""

from can import Message

TEST_TIME = 1483389946.197 # some random number

# List of messages of different types that can be used in tests
TEST_MESSAGES_BASE = [
    Message(
        # empty
    ),
    Message(
        # only data
        data=[0x00, 0x42]
    ),
    Message(
        # no data
        arbitration_id=0xAB, extended_id=False
    ),
    Message(
        # no data
        arbitration_id=0x42, extended_id=True
    ),
    Message(
        # no data
        arbitration_id=0xABCDEF,
    ),
    Message(
        # empty data
        data=[]
    ),
    Message(
        # empty data
        data=[0xFF, 0xFE, 0xFD],
    ),
    Message(
        arbitration_id=0xABCDEF, extended_id=True,
        timestamp=TEST_TIME,
        data=[1, 2, 3, 4, 5, 6, 7, 8]
    ),
    Message(
        arbitration_id=0x123, extended_id=False,
        timestamp=TEST_TIME + 42.42,
        data=[0xff, 0xff]
    ),
    Message(
        arbitration_id=0xDADADA, extended_id=True,
        timestamp=TEST_TIME + .165,
        data=[1, 2, 3, 4, 5, 6, 7, 8]
    ),
    Message(
        arbitration_id=0x123, extended_id=False,
        timestamp=TEST_TIME + .365,
        data=[254, 255]
    ),
    Message(
        arbitration_id=0x768, extended_id=False,
        timestamp=TEST_TIME + 3.165
    ),
]

TEST_MESSAGES_REMOTE_FRAMES = [
    Message(
        arbitration_id=0xDADADA, extended_id=True, is_remote_frame=False,
        timestamp=TEST_TIME + .165,
        data=[1, 2, 3, 4, 5, 6, 7, 8]
    ),
    Message(
        arbitration_id=0x123, extended_id=False, is_remote_frame=False,
        timestamp=TEST_TIME + .365,
        data=[254, 255]
    ),
    Message(
        arbitration_id=0x768, extended_id=False, is_remote_frame=True,
        timestamp=TEST_TIME + 3.165
    ),
    Message(
        arbitration_id=0xABCDEF, extended_id=True, is_remote_frame=True,
        timestamp=TEST_TIME + 7858.67
    ),
]

TEST_MESSAGES_ERROR_FRAMES = [
    Message(
        is_error_frame=True
    ),
    Message(
        is_error_frame=True,
        timestamp=TEST_TIME + 0.170
    ),
    Message(
        is_error_frame=True,
        timestamp=TEST_TIME + 17.157
    )
]

TEST_COMMENTS = [
    "This is the first comment",
    "", # empty comment
    "This third comment contains some strange characters: 'ä\"§$%&/()=?__::_Öüßêè and ends here.",
    (
        "This fourth comment is quite long! " \
        "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero eos et accusam et justo duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet. " \
        "Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. " \
        "Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla facilisi." \
    )
]

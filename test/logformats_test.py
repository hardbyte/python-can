#!/usr/bin/env python

"""
This test module test the separate reader/writer combinations of the can.io.*
modules by writing some messages to a temporary file and reading it again.
Then it checks if the messages that were read are same ones as the
ones that were written. It also checks that the order of the messages
is correct. The types of messages that are tested differs between the
different writer/reader pairs - e.g., some don't handle error frames and
comments.

TODO: correctly set preserves_channel and adds_default_channel
"""
import logging
import unittest
from parameterized import parameterized
import tempfile
import os
from abc import abstractmethod, ABCMeta
from itertools import zip_longest
from datetime import datetime

import can
from can.io import blf

from .data.example_data import (
    TEST_MESSAGES_BASE,
    TEST_MESSAGES_REMOTE_FRAMES,
    TEST_MESSAGES_ERROR_FRAMES,
    TEST_MESSAGES_CAN_FD,
    TEST_COMMENTS,
    sort_messages,
)
from .message_helper import ComparingMessagesTestCase

logging.basicConfig(level=logging.DEBUG)


class ReaderWriterExtensionTest(unittest.TestCase):
    message_writers_and_readers = {}
    for suffix, writer in can.Logger.message_writers.items():
        message_writers_and_readers[suffix] = (
            writer,
            can.LogReader.message_readers.get(suffix),
        )

    def test_extension_matching(self):
        for suffix, (writer, reader) in self.message_writers_and_readers.items():
            suffix_variants = [
                suffix.upper(),
                suffix.lower(),
                f"can.msg.ext{suffix}",
                "".join([c.upper() if i % 2 else c for i, c in enumerate(suffix)]),
            ]
            for suffix_variant in suffix_variants:
                tmp_file = tempfile.NamedTemporaryFile(
                    suffix=suffix_variant, delete=False
                )
                tmp_file.close()
                try:
                    with can.Logger(tmp_file.name) as logger:
                        assert type(logger) == writer
                    if reader is not None:
                        with can.LogReader(tmp_file.name) as player:
                            assert type(player) == reader
                finally:
                    os.remove(tmp_file.name)


class ReaderWriterTest(unittest.TestCase, ComparingMessagesTestCase, metaclass=ABCMeta):
    """Tests a pair of writer and reader by writing all data first and
    then reading all data and checking if they could be reconstructed
    correctly. Optionally writes some comments as well.

    .. note::
        This class is prevented from being executed as a test
        case itself by a *del* statement in at the end of the file.
        (Source: `*Wojciech B.* on StackOverlfow <https://stackoverflow.com/a/22836015/3753684>`_)
    """

    def __init__(self, *args, **kwargs):
        unittest.TestCase.__init__(self, *args, **kwargs)
        self._setup_instance()

    @abstractmethod
    def _setup_instance(self):
        """Hook for subclasses."""
        raise NotImplementedError()

    def _setup_instance_helper(
        self,
        writer_constructor,
        reader_constructor,
        binary_file=False,
        check_remote_frames=True,
        check_error_frames=True,
        check_fd=True,
        check_comments=False,
        test_append=False,
        allowed_timestamp_delta=0.0,
        preserves_channel=True,
        adds_default_channel=None,
    ):
        """
        :param Callable writer_constructor: the constructor of the writer class
        :param Callable reader_constructor: the constructor of the reader class
        :param bool binary_file: if True, opens files in binary and not in text mode

        :param bool check_remote_frames: if True, also tests remote frames
        :param bool check_error_frames: if True, also tests error frames
        :param bool check_fd: if True, also tests CAN FD frames
        :param bool check_comments: if True, also inserts comments at some
                                    locations and checks if they are contained anywhere literally
                                    in the resulting file. The locations as selected randomly
                                    but deterministically, which makes the test reproducible.
        :param bool test_append: tests the writer in append mode as well

        :param float or int or None allowed_timestamp_delta: directly passed to :meth:`can.Message.equals`
        :param bool preserves_channel: if True, checks that the channel attribute is preserved
        :param any adds_default_channel: sets this as the channel when not other channel was given
                                         ignored, if *preserves_channel* is True
        """
        # get all test messages
        self.original_messages = list(TEST_MESSAGES_BASE)
        if check_remote_frames:
            self.original_messages += TEST_MESSAGES_REMOTE_FRAMES
        if check_error_frames:
            self.original_messages += TEST_MESSAGES_ERROR_FRAMES
        if check_fd:
            self.original_messages += TEST_MESSAGES_CAN_FD

        # sort them so that for example ASCWriter does not "fix" any messages with timestamp 0.0
        self.original_messages = sort_messages(self.original_messages)

        if check_comments:
            # we check this because of the lack of a common base class
            # we filter for not starts with '__' so we do not get all the builtin
            # methods when logging to the console
            attrs = [
                attr for attr in dir(writer_constructor) if not attr.startswith("__")
            ]
            assert (
                "log_event" in attrs
            ), "cannot check comments with this writer: {}".format(writer_constructor)

        # get all test comments
        self.original_comments = TEST_COMMENTS if check_comments else ()

        self.writer_constructor = writer_constructor
        self.reader_constructor = reader_constructor
        self.binary_file = binary_file
        self.test_append_enabled = test_append

        ComparingMessagesTestCase.__init__(
            self,
            allowed_timestamp_delta=allowed_timestamp_delta,
            preserves_channel=preserves_channel,
        )
        # adds_default_channel=adds_default_channel # TODO inlcude in tests

    def setUp(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as test_file:
            self.test_file_name = test_file.name

    def tearDown(self):
        os.remove(self.test_file_name)
        del self.test_file_name

    def test_path_like_explicit_stop(self):
        """testing with path-like and explicit stop() call"""

        # create writer
        print("writing all messages/comments")
        writer = self.writer_constructor(self.test_file_name)
        self._write_all(writer)
        self._ensure_fsync(writer)
        writer.stop()
        if hasattr(writer.file, "closed"):
            self.assertTrue(writer.file.closed)

        print("reading all messages")
        reader = self.reader_constructor(self.test_file_name)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()
        if hasattr(writer.file, "closed"):
            self.assertTrue(writer.file.closed)

        # check if at least the number of messages matches
        # could use assertCountEqual in later versions of Python and in the other methods
        self.assertEqual(
            len(read_messages),
            len(self.original_messages),
            "the number of written messages does not match the number of read messages",
        )

        self.assertMessagesEqual(self.original_messages, read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_path_like_context_manager(self):
        """testing with path-like object and context manager"""

        # create writer
        print("writing all messages/comments")
        with self.writer_constructor(self.test_file_name) as writer:
            self._write_all(writer)
            self._ensure_fsync(writer)
            w = writer
        if hasattr(w.file, "closed"):
            self.assertTrue(w.file.closed)

        # read all written messages
        print("reading all messages")
        with self.reader_constructor(self.test_file_name) as reader:
            read_messages = list(reader)
            r = reader
        if hasattr(r.file, "closed"):
            self.assertTrue(r.file.closed)

        # check if at least the number of messages matches;
        self.assertEqual(
            len(read_messages),
            len(self.original_messages),
            "the number of written messages does not match the number of read messages",
        )

        self.assertMessagesEqual(self.original_messages, read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_file_like_explicit_stop(self):
        """testing with file-like object and explicit stop() call"""

        # create writer
        print("writing all messages/comments")
        my_file = open(self.test_file_name, "wb" if self.binary_file else "w")
        writer = self.writer_constructor(my_file)
        self._write_all(writer)
        self._ensure_fsync(writer)
        writer.stop()
        if hasattr(my_file, "closed"):
            self.assertTrue(my_file.closed)

        print("reading all messages")
        my_file = open(self.test_file_name, "rb" if self.binary_file else "r")
        reader = self.reader_constructor(my_file)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()
        if hasattr(my_file, "closed"):
            self.assertTrue(my_file.closed)

        # check if at least the number of messages matches
        # could use assertCountEqual in later versions of Python and in the other methods
        self.assertEqual(
            len(read_messages),
            len(self.original_messages),
            "the number of written messages does not match the number of read messages",
        )

        self.assertMessagesEqual(self.original_messages, read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_file_like_context_manager(self):
        """testing with file-like object and context manager"""

        # create writer
        print("writing all messages/comments")
        my_file = open(self.test_file_name, "wb" if self.binary_file else "w")
        with self.writer_constructor(my_file) as writer:
            self._write_all(writer)
            self._ensure_fsync(writer)
            w = writer
        if hasattr(my_file, "closed"):
            self.assertTrue(my_file.closed)

        # read all written messages
        print("reading all messages")
        my_file = open(self.test_file_name, "rb" if self.binary_file else "r")
        with self.reader_constructor(my_file) as reader:
            read_messages = list(reader)
            r = reader
        if hasattr(my_file, "closed"):
            self.assertTrue(my_file.closed)

        # check if at least the number of messages matches;
        self.assertEqual(
            len(read_messages),
            len(self.original_messages),
            "the number of written messages does not match the number of read messages",
        )

        self.assertMessagesEqual(self.original_messages, read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_append_mode(self):
        """
        testing append mode with context manager and path-like object
        """
        if not self.test_append_enabled:
            raise unittest.SkipTest("do not test append mode")

        count = len(self.original_messages)
        first_part = self.original_messages[: count // 2]
        second_part = self.original_messages[count // 2 :]

        # write first half
        with self.writer_constructor(self.test_file_name) as writer:
            for message in first_part:
                writer(message)
            self._ensure_fsync(writer)

        # use append mode for second half
        try:
            writer = self.writer_constructor(self.test_file_name, append=True)
        except ValueError as e:
            # maybe "append" is not a formal parameter (this is the case for SqliteWriter)
            try:
                writer = self.writer_constructor(self.test_file_name)
            except TypeError:
                # if it is still a problem, raise the initial error
                raise e
        with writer:
            for message in second_part:
                writer(message)
            self._ensure_fsync(writer)
        with self.reader_constructor(self.test_file_name) as reader:
            read_messages = list(reader)

        self.assertMessagesEqual(self.original_messages, read_messages)

    def _write_all(self, writer):
        """Writes messages and insert comments here and there."""
        # Note: we make no assumptions about the length of original_messages and original_comments
        for msg, comment in zip_longest(
            self.original_messages, self.original_comments, fillvalue=None
        ):
            # msg and comment might be None
            if comment is not None:
                print("writing comment: ", comment)
                writer.log_event(comment)  # we already know that this method exists
            if msg is not None:
                print("writing message: ", msg)
                writer(msg)

    def _ensure_fsync(self, io_handler):
        if hasattr(io_handler.file, "fileno"):
            io_handler.file.flush()
            os.fsync(io_handler.file.fileno())

    def assertIncludesComments(self, filename):
        """
        Ensures that all comments are literally contained in the given file.

        :param filename: the path-like object to use
        """
        if self.original_comments:
            # read the entire outout file
            with open(filename, "rb" if self.binary_file else "r") as file:
                output_contents = file.read()
            # check each, if they can be found in there literally
            for comment in self.original_comments:
                self.assertIn(comment, output_contents)


class TestAscFileFormat(ReaderWriterTest):
    """Tests can.ASCWriter and can.ASCReader"""

    FORMAT_START_OF_FILE_DATE = "%a %b %d %I:%M:%S.%f %p %Y"

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.ASCWriter,
            can.ASCReader,
            check_fd=True,
            check_comments=True,
            preserves_channel=False,
            adds_default_channel=0,
        )

    def _read_log_file(self, filename, **kwargs):
        logfile = os.path.join(os.path.dirname(__file__), "data", filename)
        with can.ASCReader(logfile, **kwargs) as reader:
            return list(reader)

    def test_absolute_time(self):
        time_from_file = "Sat Sep 30 10:06:13.191 PM 2017"
        start_time = datetime.strptime(
            time_from_file, self.FORMAT_START_OF_FILE_DATE
        ).timestamp()

        expected_messages = [
            can.Message(
                timestamp=2.5010 + start_time,
                arbitration_id=0xC8,
                is_extended_id=False,
                is_rx=False,
                channel=1,
                dlc=8,
                data=[9, 8, 7, 6, 5, 4, 3, 2],
            ),
            can.Message(
                timestamp=17.876708 + start_time,
                arbitration_id=0x6F9,
                is_extended_id=False,
                channel=0,
                dlc=0x8,
                data=[5, 0xC, 0, 0, 0, 0, 0, 0],
            ),
        ]
        actual = self._read_log_file("test_CanMessage.asc", relative_timestamp=False)
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_message(self):
        expected_messages = [
            can.Message(
                timestamp=2.5010,
                arbitration_id=0xC8,
                is_extended_id=False,
                is_rx=False,
                channel=1,
                dlc=8,
                data=[9, 8, 7, 6, 5, 4, 3, 2],
            ),
            can.Message(
                timestamp=17.876708,
                arbitration_id=0x6F9,
                is_extended_id=False,
                channel=0,
                dlc=0x8,
                data=[5, 0xC, 0, 0, 0, 0, 0, 0],
            ),
        ]
        actual = self._read_log_file("test_CanMessage.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_remote_message(self):
        expected_messages = [
            can.Message(
                timestamp=2.510001,
                arbitration_id=0x100,
                is_extended_id=False,
                channel=1,
                is_remote_frame=True,
            ),
            can.Message(
                timestamp=2.520002,
                arbitration_id=0x200,
                is_extended_id=False,
                is_rx=False,
                channel=2,
                is_remote_frame=True,
            ),
            can.Message(
                timestamp=2.584921,
                arbitration_id=0x300,
                is_extended_id=False,
                channel=3,
                dlc=8,
                is_remote_frame=True,
            ),
        ]
        actual = self._read_log_file("test_CanRemoteMessage.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_fd_remote_message(self):
        expected_messages = [
            can.Message(
                timestamp=30.300981,
                arbitration_id=0x50005,
                channel=2,
                dlc=5,
                is_rx=False,
                is_fd=True,
                is_remote_frame=True,
                error_state_indicator=True,
            )
        ]
        actual = self._read_log_file("test_CanFdRemoteMessage.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_fd_message(self):
        expected_messages = [
            can.Message(
                timestamp=30.005021,
                arbitration_id=0x300,
                is_extended_id=False,
                channel=0,
                dlc=8,
                data=[0x11, 0xC2, 3, 4, 5, 6, 7, 8],
                is_fd=True,
                bitrate_switch=True,
            ),
            can.Message(
                timestamp=30.005041,
                arbitration_id=0x1C4D80A7,
                channel=1,
                dlc=8,
                is_rx=False,
                data=[0x12, 0xC2, 3, 4, 5, 6, 7, 8],
                is_fd=True,
                error_state_indicator=True,
            ),
            can.Message(
                timestamp=30.005071,
                arbitration_id=0x30A,
                is_extended_id=False,
                channel=2,
                dlc=8,
                data=[1, 2, 3, 4, 5, 6, 7, 8],
                is_fd=True,
                bitrate_switch=True,
                error_state_indicator=True,
            ),
        ]
        actual = self._read_log_file("test_CanFdMessage.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_fd_message_64(self):
        expected_messages = [
            can.Message(
                timestamp=30.506898,
                arbitration_id=0x4EE,
                is_extended_id=False,
                channel=3,
                dlc=64,
                data=[0xA1, 2, 3, 4] + 59 * [0] + [0x64],
                is_fd=True,
                error_state_indicator=True,
            ),
            can.Message(
                timestamp=31.506898,
                arbitration_id=0x1C4D80A7,
                channel=3,
                dlc=64,
                data=[0xB1, 2, 3, 4] + 59 * [0] + [0x64],
                is_fd=True,
                bitrate_switch=True,
            ),
        ]
        actual = self._read_log_file("test_CanFdMessage64.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_can_and_canfd_error_frames(self):
        expected_messages = [
            can.Message(timestamp=2.501000, channel=0, is_error_frame=True),
            can.Message(timestamp=3.501000, channel=0, is_error_frame=True),
            can.Message(timestamp=4.501000, channel=1, is_error_frame=True),
            can.Message(
                timestamp=30.806898,
                channel=4,
                is_rx=False,
                is_error_frame=True,
                is_fd=True,
            ),
        ]
        actual = self._read_log_file("test_CanErrorFrames.asc")
        self.assertMessagesEqual(actual, expected_messages)

    def test_ignore_comments(self):
        _msg_list = self._read_log_file("logfile.asc")

    def test_no_triggerblock(self):
        _msg_list = self._read_log_file("issue_1256.asc")

    def test_can_dlc_greater_than_8(self):
        _msg_list = self._read_log_file("issue_1299.asc")


class TestBlfFileFormat(ReaderWriterTest):
    """Tests can.BLFWriter and can.BLFReader.

    Uses log files created by Toby Lorenz:
    https://bitbucket.org/tobylorenz/vector_blf/src/master/src/Vector/BLF/tests/unittests/events_from_binlog/
    """

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.BLFWriter,
            can.BLFReader,
            binary_file=True,
            check_fd=True,
            check_comments=False,
            test_append=True,
            allowed_timestamp_delta=1.0e-6,
            preserves_channel=False,
            adds_default_channel=0,
        )

    def _read_log_file(self, filename):
        logfile = os.path.join(os.path.dirname(__file__), "data", filename)
        with can.BLFReader(logfile) as reader:
            return list(reader)

    def test_can_message(self):
        expected = can.Message(
            timestamp=2459565876.494607,
            arbitration_id=0x4444444,
            is_extended_id=False,
            channel=0x1110,
            dlc=0x33,
            data=[0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC],
        )
        actual = self._read_log_file("test_CanMessage.blf")
        self.assertMessagesEqual(actual, [expected] * 2)
        self.assertEqual(actual[0].channel, expected.channel)

    def test_can_message_2(self):
        expected = can.Message(
            timestamp=2459565876.494607,
            arbitration_id=0x4444444,
            is_extended_id=False,
            channel=0x1110,
            dlc=0x33,
            data=[0x55, 0x66, 0x77, 0x88, 0x99, 0xAA, 0xBB, 0xCC],
        )
        actual = self._read_log_file("test_CanMessage2.blf")
        self.assertMessagesEqual(actual, [expected] * 2)
        self.assertEqual(actual[0].channel, expected.channel)

    def test_can_fd_message(self):
        expected = can.Message(
            timestamp=2459565876.494607,
            arbitration_id=0x4444444,
            is_extended_id=False,
            channel=0x1110,
            dlc=64,
            is_fd=True,
            bitrate_switch=True,
            error_state_indicator=True,
            data=range(64),
        )
        actual = self._read_log_file("test_CanFdMessage.blf")
        self.assertMessagesEqual(actual, [expected] * 2)
        self.assertEqual(actual[0].channel, expected.channel)

    def test_can_fd_message_64(self):
        expected = can.Message(
            timestamp=2459565876.494607,
            arbitration_id=0x15555555,
            is_extended_id=False,
            is_remote_frame=True,
            channel=0x10,
            dlc=64,
            is_fd=True,
            is_rx=False,
            bitrate_switch=True,
            error_state_indicator=True,
        )
        actual = self._read_log_file("test_CanFdMessage64.blf")
        self.assertMessagesEqual(actual, [expected] * 2)
        self.assertEqual(actual[0].channel, expected.channel)

    def test_can_error_frame_ext(self):
        expected = can.Message(
            timestamp=2459565876.494607,
            is_error_frame=True,
            arbitration_id=0x19999999,
            is_extended_id=True,
            channel=0x1110,
            dlc=0x66,
            data=[0xCC, 0xDD, 0xEE, 0xFF, 0x11, 0x22, 0x33, 0x44],
        )
        actual = self._read_log_file("test_CanErrorFrameExt.blf")
        self.assertMessagesEqual(actual, [expected] * 2)
        self.assertEqual(actual[0].channel, expected.channel)

    def test_timestamp_to_systemtime(self):
        self.assertAlmostEqual(
            1636485425.999,
            blf.systemtime_to_timestamp(blf.timestamp_to_systemtime(1636485425.998908)),
            places=3,
        )
        self.assertAlmostEqual(
            1636485426.0,
            blf.systemtime_to_timestamp(blf.timestamp_to_systemtime(1636485425.999908)),
            places=3,
        )


class TestCanutilsFileFormat(ReaderWriterTest):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.CanutilsLogWriter,
            can.CanutilsLogReader,
            check_fd=True,
            test_append=True,
            check_comments=False,
            preserves_channel=False,
            adds_default_channel="vcan0",
        )


class TestCsvFileFormat(ReaderWriterTest):
    """Tests can.CSVWriter and can.CSVReader"""

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.CSVWriter,
            can.CSVReader,
            check_fd=False,
            test_append=True,
            check_comments=False,
            preserves_channel=False,
            adds_default_channel=None,
        )


class TestSqliteDatabaseFormat(ReaderWriterTest):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.SqliteWriter,
            can.SqliteReader,
            check_fd=False,
            test_append=True,
            check_comments=False,
            preserves_channel=False,
            adds_default_channel=None,
        )

    @unittest.skip("not implemented")
    def test_file_like_explicit_stop(self):
        pass

    @unittest.skip("not implemented")
    def test_file_like_context_manager(self):
        pass

    def test_read_all(self):
        """
        testing :meth:`can.SqliteReader.read_all` with context manager and path-like object
        """
        # create writer
        print("writing all messages/comments")
        with self.writer_constructor(self.test_file_name) as writer:
            self._write_all(writer)

        # read all written messages
        print("reading all messages")
        with self.reader_constructor(self.test_file_name) as reader:
            read_messages = list(reader.read_all())

        # check if at least the number of messages matches;
        self.assertEqual(
            len(read_messages),
            len(self.original_messages),
            "the number of written messages does not match the number of read messages",
        )

        self.assertMessagesEqual(self.original_messages, read_messages)


class TestPrinter(unittest.TestCase):
    """Tests that can.Printer does not crash.

    TODO test append mode
    """

    messages = (
        TEST_MESSAGES_BASE
        + TEST_MESSAGES_REMOTE_FRAMES
        + TEST_MESSAGES_ERROR_FRAMES
        + TEST_MESSAGES_CAN_FD
    )

    def test_not_crashes_with_stdout(self):
        with can.Printer() as printer:
            for message in self.messages:
                printer(message)

    def test_not_crashes_with_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as temp_file:
            with can.Printer(temp_file) as printer:
                for message in self.messages:
                    printer(message)


class TestTrcFileFormatBase(ReaderWriterTest):
    """
    Base class for Tests with can.TRCWriter and can.TRCReader

    .. note::
        This class is prevented from being executed as a test
        case itself by a *del* statement in at the end of the file.
    """

    def _setup_instance(self):
        super()._setup_instance_helper(
            can.TRCWriter,
            can.TRCReader,
            check_remote_frames=False,
            check_error_frames=False,
            check_fd=False,
            check_comments=False,
            preserves_channel=False,
            allowed_timestamp_delta=0.001,
            adds_default_channel=0,
        )

    def _read_log_file(self, filename, **kwargs):
        logfile = os.path.join(os.path.dirname(__file__), "data", filename)
        with can.TRCReader(logfile, **kwargs) as reader:
            return list(reader)


class TestTrcFileFormatGen(TestTrcFileFormatBase):
    """Generic tests for can.TRCWriter and can.TRCReader with different file versions"""

    def test_can_message(self):
        expected_messages = [
            can.Message(
                timestamp=2.5010,
                arbitration_id=0xC8,
                is_extended_id=False,
                is_rx=False,
                channel=1,
                dlc=8,
                data=[9, 8, 7, 6, 5, 4, 3, 2],
            ),
            can.Message(
                timestamp=17.876708,
                arbitration_id=0x6F9,
                is_extended_id=False,
                channel=0,
                dlc=0x8,
                data=[5, 0xC, 0, 0, 0, 0, 0, 0],
            ),
        ]
        actual = self._read_log_file("test_CanMessage.trc")
        self.assertMessagesEqual(actual, expected_messages)

    @parameterized.expand(
        [
            ("V1_0", "test_CanMessage_V1_0_BUS1.trc", False),
            ("V1_1", "test_CanMessage_V1_1.trc", True),
            ("V2_1", "test_CanMessage_V2_1.trc", True),
        ]
    )
    def test_can_message_versions(self, name, filename, is_rx_support):
        with self.subTest(name):

            def msg_std(timestamp):
                msg = can.Message(
                    timestamp=timestamp,
                    arbitration_id=0x000,
                    is_extended_id=False,
                    channel=1,
                    dlc=8,
                    data=[0, 0, 0, 0, 0, 0, 0, 0],
                )
                if is_rx_support:
                    msg.is_rx = False
                return msg

            def msg_ext(timestamp):
                msg = can.Message(
                    timestamp=timestamp,
                    arbitration_id=0x100,
                    is_extended_id=True,
                    channel=1,
                    dlc=8,
                    data=[0, 0, 0, 0, 0, 0, 0, 0],
                )
                if is_rx_support:
                    msg.is_rx = False
                return msg

            expected_messages = [
                msg_ext(17.5354),
                msg_ext(17.7003),
                msg_ext(17.8738),
                msg_std(19.2954),
                msg_std(19.5006),
                msg_std(19.7052),
                msg_ext(20.5927),
                msg_ext(20.7986),
                msg_ext(20.9560),
                msg_ext(21.0971),
            ]
            actual = self._read_log_file(filename)
            self.assertMessagesEqual(actual, expected_messages)

    def test_not_supported_version(self):
        with self.assertRaises(NotImplementedError):
            writer = can.TRCWriter("test.trc")
            writer.file_version = can.TRCFileVersion.UNKNOWN
            writer.on_message_received(can.Message())


class TestTrcFileFormatV1_0(TestTrcFileFormatBase):
    """Tests can.TRCWriter and can.TRCReader with file version 1.0"""

    @staticmethod
    def Writer(filename):
        writer = can.TRCWriter(filename)
        writer.file_version = can.TRCFileVersion.V1_0
        return writer

    def _setup_instance(self):
        super()._setup_instance()
        self.writer_constructor = TestTrcFileFormatV1_0.Writer


# this excludes the base class from being executed as a test case itself
del ReaderWriterTest
del TestTrcFileFormatBase


if __name__ == "__main__":
    unittest.main()

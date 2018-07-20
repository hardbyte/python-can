#!/usr/bin/env python
# coding: utf-8

"""
This test module test the separate reader/writer combinations of the can.io.*
modules by writing some messages to a temporary file and reading it again.
Then it checks if the messages that were read are same ones as the
ones that were written. It also checks that the order of the messages
is correct. The types of messages that are tested differs between the
different writer/reader pairs - e.g., some don't handle error frames and
comments.

TODO: implement CAN FD support testing
"""

from __future__ import print_function, absolute_import, division

import unittest
import tempfile
import os
from abc import abstractmethod, ABCMeta

try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

import can

from .data.example_data import TEST_MESSAGES_BASE, TEST_MESSAGES_REMOTE_FRAMES, \
                               TEST_MESSAGES_ERROR_FRAMES, TEST_COMMENTS


class ReaderWriterTest(unittest.TestCase):
    """Tests a pair of writer and reader by writing all data first and
    then reading all data and checking if they could be reconstructed
    correctly. Optionally writes some comments as well.

    """

    __test__ = False

    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(ReaderWriterTest, self).__init__(*args, **kwargs)
        self._setup_instance()

    @abstractmethod
    def _setup_instance(self):
        """Hook for subclasses."""
        raise NotImplementedError()

    def _setup_instance_helper(self,
            writer_constructor, reader_constructor, binary_file=False,
            check_remote_frames=True, check_error_frames=True, check_comments=False,
            test_append=False, round_timestamps=False):
        """
        :param Callable writer_constructor: the constructor of the writer class
        :param Callable reader_constructor: the constructor of the reader class

        :param bool check_remote_frames: if True, also tests remote frames
        :param bool check_error_frames: if True, also tests error frames
        :param bool check_comments: if True, also inserts comments at some
                                    locations and checks if they are contained anywhere literally
                                    in the resulting file. The locations as selected randomly
                                    but deterministically, which makes the test reproducible.
        :param bool test_append: tests the writer in append mode as well
        :param bool round_timestamps: if True, rounds timestamps using :meth:`~builtin.round`
                                      before comparing the read messages/events

        """
        # get all test messages
        self.original_messages = TEST_MESSAGES_BASE
        if check_remote_frames:
            self.original_messages += TEST_MESSAGES_REMOTE_FRAMES
        if check_error_frames:
            self.original_messages += TEST_MESSAGES_ERROR_FRAMES

        if check_comments:
            # we check this because of the lack of a common base class
            # we filter for not starts with '__' so we do not get all the builtin
            # methods when logging to the console
            attrs = [attr for attr in dir(writer_constructor) if not attr.startswith('__')]
            assert 'log_event' in attrs, \
                "cannot check comments with this writer: {}".format(writer_constructor)

        # get all test comments
        self.original_comments = TEST_COMMENTS if check_comments else ()

        self.writer_constructor = writer_constructor
        self.reader_constructor = reader_constructor
        self.binary_file = binary_file
        self.test_append_enabled = test_append
        self.round_timestamps = round_timestamps

    def setUp(self):
        with tempfile.NamedTemporaryFile('w+', delete=False) as test_file:
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
        if hasattr(writer.file, 'closed'):
            self.assertTrue(writer.file.closed)

        print("reading all messages")
        reader = self.reader_constructor(self.test_file_name)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()
        if hasattr(writer.file, 'closed'):
            self.assertTrue(writer.file.closed)

        # check if at least the number of messages matches
        # could use assertCountEqual in later versions of Python and in the other methods
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_path_like_context_manager(self):
        """testing with path-like object and context manager"""

        # create writer
        print("writing all messages/comments")
        with self.writer_constructor(self.test_file_name) as writer:
            self._write_all(writer)
            self._ensure_fsync(writer)
            w = writer
        if hasattr(w.file, 'closed'):
            self.assertTrue(w.file.closed)

        # read all written messages
        print("reading all messages")
        with self.reader_constructor(self.test_file_name) as reader:
            read_messages = list(reader)
            r = reader
        if hasattr(r.file, 'closed'):
            self.assertTrue(r.file.closed)

        # check if at least the number of messages matches; 
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_file_like_explicit_stop(self):
        """testing with file-like object and explicit stop() call"""

        # create writer
        print("writing all messages/comments")
        my_file = open(self.test_file_name, 'wb' if self.binary_file else 'w')
        writer = self.writer_constructor(my_file)
        self._write_all(writer)
        self._ensure_fsync(writer)
        writer.stop()
        if hasattr(my_file, 'closed'):
            self.assertTrue(my_file.closed)

        print("reading all messages")
        my_file = open(self.test_file_name, 'rb' if self.binary_file else 'r')
        reader = self.reader_constructor(my_file)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()
        if hasattr(my_file, 'closed'):
            self.assertTrue(my_file.closed)

        # check if at least the number of messages matches
        # could use assertCountEqual in later versions of Python and in the other methods
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_file_like_context_manager(self):
        """testing with file-like object and context manager"""

        # create writer
        print("writing all messages/comments")
        my_file = open(self.test_file_name, 'wb' if self.binary_file else 'w')
        with self.writer_constructor(my_file) as writer:
            self._write_all(writer)
            self._ensure_fsync(writer)
            w = writer
        if hasattr(my_file, 'closed'):
            self.assertTrue(my_file.closed)

        # read all written messages
        print("reading all messages")
        my_file = open(self.test_file_name, 'rb' if self.binary_file else 'r')
        with self.reader_constructor(my_file) as reader:
            read_messages = list(reader)
            r = reader
        if hasattr(my_file, 'closed'):
            self.assertTrue(my_file.closed)

        # check if at least the number of messages matches; 
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(self.test_file_name)

    def test_append_mode(self):
        """
        testing append mode with context manager and path-like object
        """
        if not self.test_append_enabled:
            raise unittest.SkipTest("do not test append mode")

        count = len(self.original_messages)
        first_part = self.original_messages[:count //  2]
        second_part = self.original_messages[count //  2:]

        # write first half
        with self.writer_constructor(self.test_file_name) as writer:
            for message in first_part:
                writer(message)
            self._ensure_fsync(writer)

        # use append mode for second half
        try:
            writer = self.writer_constructor(self.test_file_name, append=True)
        except TypeError as e:
            # maybe "append" is not a formal parameter
            try:
                writer = self.writer_constructor(self.test_file_name)
            except TypeError:
                # is the is still a problem, raise the initial error
                raise e
        with writer:
            for message in second_part:
                writer(message)
            self._ensure_fsync(writer)
        with self.reader_constructor(self.test_file_name) as reader:
            read_messages = list(reader)

        self.assertMessagesEqual(read_messages)

    def _write_all(self, writer):
        """Writes messages and insert comments here and there."""
        # Note: we make no assumptions about the length of original_messages and original_comments
        for msg, comment in zip_longest(self.original_messages, self.original_comments, fillvalue=None):
            # msg and comment might be None
            if comment is not None:
                print("writing comment: ", comment)
                writer.log_event(comment) # we already know that this method exists
            if msg is not None:
                print("writing message: ", msg)
                writer(msg)

    def _ensure_fsync(self, io_handler):
        if hasattr(io_handler.file, 'fileno'):
            io_handler.file.flush()
            os.fsync(io_handler.file.fileno())

    def assertMessagesEqual(self, read_messages):
        """
        Checks the order and content of the individual messages.
        """
        for index, (original, read) in enumerate(zip(self.original_messages, read_messages)):
            try:
                # check everything except the timestamp
                self.assertEqual(original, read, "messages are not equal at index #{}".format(index))
                # check the timestamp
                if self.round_timestamps:
                    original.timestamp = round(original.timestamp)
                    read.timestamp = round(read.timestamp)
                self.assertAlmostEqual(read.timestamp, original.timestamp, places=6,
                    msg="message timestamps are not almost_equal at index #{} ({!r} !~= {!r})"
                        .format(index, original.timestamp, read.timestamp))
            except:
                print("Comparing: original message: {!r}".format(original))
                print("           read     message: {!r}".format(read))
                raise

    def assertIncludesComments(self, filename):
        """
        Ensures that all comments are literally contained in the given file.

        :param filename: the path-like object to use
        """
        if self.original_comments:
            # read the entire outout file
            with open(filename, 'rb' if self.binary_file else 'r') as file:
                output_contents = file.read()
            # check each, if they can be found in there literally
            for comment in self.original_comments:
                self.assertIn(comment, output_contents)


class TestAscFileFormat(ReaderWriterTest):
    """Tests can.ASCWriter and can.ASCReader"""

    __test__ = True

    def _setup_instance(self):
        super(TestAscFileFormat, self)._setup_instance_helper(
            can.ASCWriter, can.ASCReader,
            check_comments=True, round_timestamps=True
        )


class TestBlfFileFormat(ReaderWriterTest):
    """Tests can.BLFWriter and can.BLFReader"""

    __test__ = True

    def _setup_instance(self):
        super(TestBlfFileFormat, self)._setup_instance_helper(
            can.BLFWriter, can.BLFReader,
            binary_file=True,
            check_comments=False
        )

    def test_read_known_file(self):
        logfile = os.path.join(os.path.dirname(__file__), "data", "logfile.blf")
        with can.BLFReader(logfile) as reader:
            messages = list(reader)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0],
                         can.Message(
                             extended_id=False,
                             arbitration_id=0x64,
                             data=[0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8]))
        self.assertEqual(messages[0].channel, 0)
        self.assertEqual(messages[1],
                         can.Message(
                             is_error_frame=True,
                             extended_id=True,
                             arbitration_id=0x1FFFFFFF))
        self.assertEqual(messages[1].channel, 0)


class TestCanutilsFileFormat(ReaderWriterTest):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    __test__ = True

    def _setup_instance(self):
        super(TestCanutilsFileFormat, self)._setup_instance_helper(
            can.CanutilsLogWriter, can.CanutilsLogReader,
            test_append=True, check_comments=False
        )


class TestCsvFileFormat(ReaderWriterTest):
    """Tests can.ASCWriter and can.ASCReader"""

    __test__ = True

    def _setup_instance(self):
        super(TestCsvFileFormat, self)._setup_instance_helper(
            can.CSVWriter, can.CSVReader,
            test_append=True, check_comments=False
        )


class TestSqliteDatabaseFormat(ReaderWriterTest):
    """Tests can.SqliteWriter and can.SqliteReader"""

    __test__ = True

    def _setup_instance(self):
        super(TestSqliteDatabaseFormat, self)._setup_instance_helper(
            can.SqliteWriter, can.SqliteReader,
            test_append=True, check_comments=False
        )

    @unittest.skip("not implemented")
    def test_file_like_explicit_stop(self):
        pass

    @unittest.skip("not implemented")
    def test_file_like_context_manager(self):
        pass


class TestPrinter(unittest.TestCase):
    """Tests that can.Printer does not crash"""

    messages = TEST_MESSAGES_BASE + TEST_MESSAGES_REMOTE_FRAMES + TEST_MESSAGES_ERROR_FRAMES

    def test_not_crashes_with_stdout(self):
        with can.Printer() as printer:
            for message in self.messages:
                printer(message)

    def test_not_crashes_with_file(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as temp_file:
            with can.Printer(temp_file) as printer:
                for message in self.messages:
                    printer(message)


if __name__ == '__main__':
    unittest.main()

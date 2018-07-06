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
import sqlite3
import os

try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

import can

from .data.example_data import TEST_MESSAGES_BASE, TEST_MESSAGES_REMOTE_FRAMES, \
                               TEST_MESSAGES_ERROR_FRAMES, TEST_COMMENTS, \
                               generate_message


class ReaderWriterTest(object):
    """Tests a pair of writer and reader by writing all data first and
    then reading all data and checking if they could be reconstructed
    correctly. Optionally writes some comments as well.

    """

    def __init__(self, writer_constructor, reader_constructor,
                 check_remote_frames=True, check_error_frames=True, check_comments=False,
                 test_append=False, round_timestamps=False,
                 *args, **kwargs):
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
        super(ReaderWriterTest, self).__init__(*args, **kwargs)

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
        self.test_append_enabled = test_append
        self.round_timestamps = round_timestamps

    def test_path_like_explicit_stop(self):
        """testing with path-like and explicit stop() call"""
        filename = self._get_temp_filename()

        # create writer
        print("writing all messages/comments")
        writer = self.writer_constructor(filename)
        self._write_all(writer)
        os.fsync(writer.file.fileno())
        writer.stop()

        print("reading all messages")
        reader = self.reader_constructor(filename)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()

        # check if at least the number of messages matches
        # could use assertCountEqual in later versions of Python and in the other methods
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(filename)

    def test_path_like_context_manager(self):
        """testing with path-like object and context manager"""
        filename = self._get_temp_filename()

        # create writer
        print("writing all messages/comments")
        with self.writer_constructor(filename) as writer:
            self._write_all(writer)
            os.fsync(writer.file.fileno())

        # read all written messages
        print("reading all messages")
        with self.reader_constructor(filename) as reader:
            read_messages = list(reader)

        # check if at least the number of messages matches; 
        self.assertEqual(len(read_messages), len(self.original_messages),
            "the number of written messages does not match the number of read messages")

        self.assertMessagesEqual(read_messages)
        self.assertIncludesComments(filename)

    def test_file_like_explicit_stop(self):
        """testing with file-like object and explicit stop() call"""
        raise unittest.SkipTest("not yet implemented")

    def test_file_like_context_manager(self):
        """testing with file-like object and context manager"""
        raise unittest.SkipTest("not yet implemented")

    def test_append_mode(self):
        """
        testing append mode with context manager and path-like object
        """
        if not self.test_append_enabled:
            raise unittest.SkipTest("do not test append mode")

        filename = self._get_temp_filename()
        count = len(self.original_messages)
        first_part = self.original_messages[:count //  2]
        second_part = self.original_messages[count //  2:]

        # write first half
        with self.writer_constructor(filename) as writer:
            for message in first_part:
                writer(message)
            os.fsync(writer.file.fileno())

        # use append mode for second half
        try:
            writer = self.writer_constructor(filename, append=True)
        except TypeError as e:
            # maybe "append" is not a formal parameter
            try:
                writer = self.writer_constructor(filename)
            except TypeError:
                # is the is still a problem, raise the initial error
                raise e
        with writer:
            for message in second_part:
                writer(message)
            os.fsync(writer.file.fileno())
        with self.reader_constructor(filename) as reader:
            read_messages = list(reader)

        self.assertMessagesEqual(read_messages)

    @staticmethod
    def _get_temp_filename():
        with tempfile.NamedTemporaryFile('w+', delete=False) as temp:
            return temp.name

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

    def assertMessagesEqual(self, read_messages):
        """
        Checks the order and content of the individual messages.
        """
        for index, (original, read) in enumerate(zip(self.original_messages, read_messages)):
            # check everything except the timestamp
            if read != original:
                # check like this to print the whole message
                print("original message: {!r}".format(original))
                print("read     message: {!r}".format(read))
                self.fail("messages are not equal at index #{}".format(index))
            # check the timestamp
            if self.round_timestamps:
                original.timestamp = round(original.timestamp)
                read.timestamp = round(read.timestamp)
            self.assertAlmostEqual(read.timestamp, original.timestamp, places=6,
                msg="message timestamps are not almost_equal at index #{} ({!r} !~= {!r})"
                    .format(index, original.timestamp, read.timestamp))

    def assertIncludesComments(self, filename):
        """
        Ensures that all comments are literally contained in the given file.

        :param filename: the path-like object to use
        """
        if self.original_comments:
            # read the entire outout file
            with open(filename, 'rt') as file:
                output_contents = file.read()
            # check each, if they can be found in there literally
            for comment in self.original_comments:
                self.assertIn(comment, output_contents)


class TestAscFileFormat(ReaderWriterTest, unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def __init__(self, *args, **kwargs):
        super(TestAscFileFormat, self).__init__(
            can.ASCWriter, can.ASCReader,
            check_comments=True, round_timestamps=True,
            *args, **kwargs
        )


class TestBlfFileFormat(ReaderWriterTest, unittest.TestCase):
    """Tests can.BLFWriter and can.BLFReader"""

    def __init__(self, *args, **kwargs):
        super(TestBlfFileFormat, self).__init__(
            can.BLFWriter, can.BLFReader,
            check_comments=False,
            *args, **kwargs
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


class TestCanutilsFileFormat(ReaderWriterTest, unittest.TestCase):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def __init__(self, *args, **kwargs):
        super(TestCanutilsFileFormat, self).__init__(
            can.CanutilsLogWriter, can.CanutilsLogReader,
            test_append=True, check_comments=False,
            *args, **kwargs
        )


class TestCsvFileFormat(ReaderWriterTest, unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def __init__(self, *args, **kwargs):
        super(TestCsvFileFormat, self).__init__(
            can.CSVWriter, can.CSVReader,
            test_append=True, check_comments=False,
            *args, **kwargs
        )


class TestSqliteDatabaseFormat(ReaderWriterTest, unittest.TestCase):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def __init__(self, *args, **kwargs):
        super(TestSqliteDatabaseFormat, self).__init__(
            can.SqliteWriter, can.SqliteReader,
            test_append=True, check_comments=False,
            *args, **kwargs
        )

    def test_writes_to_same_file(self):
        filename = self._get_temp_filename()

        with can.SqliteWriter(filename) as first_listener:
            first_listener(generate_message(0x01))
            first_listener.stop()

        with can.SqliteWriter(filename) as second_listener:
            second_listener(generate_message(0x02))
            second_listener.stop()

        with sqlite3.connect(filename) as con:
            c = con.cursor()

            c.execute("select COUNT() from messages")
            self.assertEqual(2, c.fetchone()[0])

            c.execute("select * from messages")
            msg1 = c.fetchone()
            msg2 = c.fetchone()

        self.assertEqual(msg1[1], 0x01)
        self.assertEqual(msg2[1], 0x02)


class TestPrinter(unittest.TestCase):
    """Tests that can.Printer does not crash"""

    messages = TEST_MESSAGES_BASE + TEST_MESSAGES_REMOTE_FRAMES + TEST_MESSAGES_ERROR_FRAMES

    def test_not_crashes_stdout(self):
        with can.Printer() as printer:
            for message in self.messages:
                printer(message)

    def test_not_crashed_file(self):
        with tempfile.NamedTemporaryFile('w', delete=False) as temp_file:
            with can.Printer(temp_file) as printer:
                for message in self.messages:
                    printer(message)


if __name__ == '__main__':
    unittest.main()

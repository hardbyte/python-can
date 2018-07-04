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

from __future__ import print_function, absolute_import

import unittest
import tempfile
from time import sleep
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


def _test_writer_and_reader(test_case, writer_constructor, reader_constructor,
                            check_remote_frames=True, check_error_frames=True, check_comments=False,
                            **kwargs):
    """
    :param bool check_remote_frames: if True, also tests remote frames
    :param bool check_error_frames: if True, also tests error frames
    :param bool check_comments: if True, also inserts comments at some
        locations and checks if they are contained anywhere literally
        in the resulting file. The locations as selected randomly
        but deterministically, which makes the test reproducible.
    """

    # get all test messages
    original_messages = TEST_MESSAGES_BASE
    if check_remote_frames:
        original_messages += TEST_MESSAGES_REMOTE_FRAMES
    if check_error_frames:
        original_messages += TEST_MESSAGES_ERROR_FRAMES

    if check_comments:
        # we check this because of the lack of a common base class
        # we filter for not starts with '__' so we do not get all the builtin
        # methods when logging to the console
        attrs = [attr for attr in dir(writer_constructor) if not attr.startswith('__')]
        test_case.assertIn('log_event', attrs,
            "cannot check comments with this writer: {}".format(writer_constructor))

    # get all test comments
    original_comments = TEST_COMMENTS if check_comments else ()

    # TODO: use https://docs.python.org/3/library/unittest.html#unittest.TestCase.subTest
    # once Python 2.7 gets dropped

    print("testing with path-like object and explicit stop() call")
    temp = tempfile.NamedTemporaryFile('w', delete=False)
    filename = temp.name
    temp.close()
    _test_writer_and_reader_execute(test_case, writer_constructor, reader_constructor,
                                    filename, original_messages, original_comments,
                                    use_context_manager=False, **kwargs)

    print("testing with path-like object and context manager")
    temp = tempfile.NamedTemporaryFile('w', delete=False)
    filename = temp.name
    temp.close()
    _test_writer_and_reader_execute(test_case, writer_constructor, reader_constructor,
                                    filename, original_messages, original_comments,
                                    use_context_manager=True, **kwargs)

    print("testing with file-like object and explicit stop() call")

    print("testing with file-like object and context manager")


def _test_writer_and_reader_execute(test_case, writer_constructor, reader_constructor,
                                    file, original_messages, original_comments,
                                    use_context_manager=False,
                                    sleep_time=None, round_timestamps=False):
    """Tests a pair of writer and reader by writing all data first and
    then reading all data and checking if they could be reconstructed
    correctly. Optionally writes some comments as well.

    :param unittest.TestCase test_case: the test case the use the assert methods on
    :param Callable writer_constructor: the constructor of the writer class
    :param Callable reader_constructor: the constructor of the reader class

    :param bool use_context_manager:
        if False, uses a explicit :meth:`~can.io.generic.BaseIOHandler.stop()`
        call on the reader and writer when finished, and else used the reader
        and writer as context managers

    :param float sleep_time: specifies the time to sleep after writing all messages.
                             gets ignored when set to None
    :param bool round_timestamps: if True, rounds timestamps using :meth:`~builtin.round`
                                  before comparing the read messages/events

    """

    assert isinstance(test_case, unittest.TestCase), \
        "test_case has to be a subclass of unittest.TestCase"

    def _write_all():
        # write messages and insert comments here and there
        # Note: we make no assumptions about the length of original_messages and original_comments
        for msg, comment in zip_longest(original_messages, original_comments, fillvalue=None):
            # msg and comment might be None
            if comment is not None:
                print("writing comment: ", comment)
                writer.log_event(comment) # we already know that this method exists
            if msg is not None:
                print("writing message: ", msg)
                writer(msg)

        # sleep and close the writer
        if sleep_time is not None:
            sleep(sleep_time)

    # create writer
    print("writing all messages/comments")
    if use_context_manager:
        with writer_constructor(file) as writer:
            _write_all()
    else:
        _write_all()
        writer.stop()

    # read all written messages
    print("reading all messages")
    if use_context_manager:
        with reader_constructor(file) as reader:
            read_messages = list(reader)
    else:
        reader = reader_constructor(file)
        read_messages = list(reader)
        # redundant, but this checks if stop() can be called multiple times
        reader.stop()

    # check if at least the number of messages matches
    test_case.assertEqual(len(read_messages), len(original_messages),
        "the number of written messages does not match the number of read messages")

    # check the order and content of the individual messages
    for i, (read, original) in enumerate(zip(read_messages, original_messages)):
        try:
            # check everything except the timestamp
            if read != original:
                # check like this to print the whole message
                print("original message: {}".format(original))
                print("read     message: {}".format(read))
                test_case.fail()
            # check the timestamp
            if round_timestamps:
                original.timestamp = round(original.timestamp)
                read.timestamp = round(read.timestamp)
            test_case.assertAlmostEqual(read.timestamp, original.timestamp, places=6)
        except Exception as exception:
            # attach the index
            exception.args += ("messages are not equal at index #{}".format(i), )
            raise exception

    # check if the comments are contained in the file
    if original_comments:
        # read the entire outout file
        with open(file, 'r') as file:
            output_contents = file.read()
        # check each, if they can be found in there literally
        for comment in original_comments:
            test_case.assertIn(comment, output_contents)


class TestCanutilsLog(unittest.TestCase):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.CanutilsLogWriter, can.CanutilsLogReader,
                                check_comments=False)


class TestAscFileFormat(unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.ASCWriter, can.ASCReader,
                                check_comments=True, round_timestamps=True)


class TestCsvFileFormat(unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.CSVWriter, can.CSVReader,
                                check_comments=False)


class TestSqliteDatabaseFormat(unittest.TestCase):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.SqliteWriter, can.SqliteReader,
                                sleep_time=can.SqliteWriter.MAX_TIME_BETWEEN_WRITES + 0.5,
                                check_comments=False)

    def testSQLWriterWritesToSameFile(self):
        f = tempfile.NamedTemporaryFile('w', delete=False)
        f.close()

        first_listener = can.SqliteWriter(f.name)
        first_listener(generate_message(0x01))

        sleep(first_listener.MAX_TIME_BETWEEN_WRITES)
        first_listener.stop()

        second_listener = can.SqliteWriter(f.name)
        second_listener(generate_message(0x02))

        sleep(second_listener.MAX_TIME_BETWEEN_WRITES)

        second_listener.stop()

        con = sqlite3.connect(f.name)

        with con:
            c = con.cursor()

            c.execute("select COUNT() from messages")
            self.assertEqual(2, c.fetchone()[0])

            c.execute("select * from messages")
            msg1 = c.fetchone()
            msg2 = c.fetchone()

        self.assertEqual(msg1[1], 0x01)
        self.assertEqual(msg2[1], 0x02)


class TestBlfFileFormat(unittest.TestCase):
    """Tests can.BLFWriter and can.BLFReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.BLFWriter, can.BLFReader,
                                check_comments=False)

    def test_reader(self):
        logfile = os.path.join(os.path.dirname(__file__), "data", "logfile.blf")
        messages = list(can.BLFReader(logfile))
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


if __name__ == '__main__':
    unittest.main()

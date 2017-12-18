"""
This test module test the different reader/writer combinations of the can.io.*
modules by writing some messages to a temporary file and reading it again.
Then it checks if the messages that ware read are same ones as the
ones that were written. It also checks that the order of the messages
is correct. The types of messages that are tested differs between the
different writer/reader pairs and one some, comments are inserted and read
again.
"""

import unittest
import tempfile
from time import sleep

try:
    # Python 3
    from itertools import zip_longest
except ImportError:
    # Python 2
    from itertools import izip_longest as zip_longest

import can

from data.example_data import TEST_MESSAGES_BASE, TEST_MESSAGES_REMOTE_FRAMES, \
                              TEST_MESSAGES_ERROR_FRAMES, TEST_COMMENTS

def _test_writer_and_reader(test_case, writer_constructor, reader_constructor, sleep_time=None,
                            check_remote_frames=True, check_error_frames=True,
                            check_comments=False):
    """Tests a pair of writer and reader by writing all data first and
    then reading all data and checking if they could be reconstructed
    correctly.

    :param test_case: the test case the use the assert methods on
    :param sleep_time: specifies the time to sleep after writing all messages.
        gets ignored when set to None
    :param check_remote_frames: if true, also tests remote frames
    :param check_error_frames: if true, also tests error frames
    :param check_comments: if true, also inserts comments at some
        locations and checks if they are contained anywhere literally
        in the resulting file. The locations as selected randomly
        but deterministically, which makes the test reproducible.
    """

    assert isinstance(test_case, unittest.TestCase), \
        "test_case has to be a subclass of unittest.TestCase"

    if check_comments:
        # we check this because of the lack of a common base class
        # we filter for not starts with '__' so we do not get all the builtin
        # methods when logging to the console
        test_case.assertIn('log_event', [d for d in dir(writer_constructor) if not d.startswith('__')],
            "cannot check comments with this writer: {}".format(writer_constructor))

    # create a temporary file
    temp = tempfile.NamedTemporaryFile('w', delete=False)
    temp.close()
    filename = temp.name

    # get all test messages
    original_messages = TEST_MESSAGES_BASE
    if check_remote_frames:
        original_messages += TEST_MESSAGES_REMOTE_FRAMES
    if check_error_frames:
        original_messages += TEST_MESSAGES_ERROR_FRAMES

    # get all test comments
    original_comments = TEST_COMMENTS

    # create writer
    writer = writer_constructor(filename)

    # write
    if check_comments:
        # write messages and insert comments here and there
        # Note: we make no assumptions about the length of original_messages and original_comments
        for msg, comment in zip_longest(original_messages, original_comments, fillvalue=None):
            # msg and comment might ne None
            if comment is not None:
                writer.log_event(comment) # we already know that this method exists
            if msg is not None:
                writer(msg)
    else:
        # ony write messages
        for msg in original_messages:
            writer(msg)

    # sleep and close the writer
    if sleep_time is not None:
        sleep(sleep_time)
    writer.stop()

    # read all written messages
    read_messages = list(reader_constructor(filename))

    # check if at least the number of messages matches
    test_case.assertEqual(len(read_messages), len(original_messages),
        "the number of written messages does not match the number of read messages")

    # check the order and content of the individual messages
    for i, (read, original) in enumerate(zip(read_messages, original_messages)):
        try:
            test_case.assertEqual(read, original)
            test_case.assertAlmostEqual(read.timestamp, original.timestamp)
        except Exception as exception:
            # attach the index
            exception.args += ("test failed at index #{}".format(i), )
            raise exception

    # check if the comments are contained in the file
    if check_comments:
        # read the entire outout file
        with open(filename, 'r') as file:
            output_contents = file.read()
        # check each, if they can be found in there literally
        for comment in original_comments:
            test_case.assertTrue(comment in output_contents)


class TestCanutilsLog(unittest.TestCase):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.CanutilsLogWriter, can.CanutilsLogReader,
                                check_error_frames=False, # TODO this should get fixed, see Issue #217
                                check_comments=False)


class TestAscFileFormat(unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.ASCWriter, can.ASCReader,
                                check_error_frames=False, # TODO this should get fixed, see Issue #218
                                check_comments=True)


class TestSqlFileFormat(unittest.TestCase):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.SqliteWriter, can.SqlReader,
                                sleep_time=0.5,
                                check_comments=False)

class TestBlfFileFormat(unittest.TestCase):
    """Tests can.BLFWriter and can.BLFReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.BLFWriter, can.BLFReader,
                                sleep_time=None,
                                check_comments=False)


if __name__ == '__main__':
    unittest.main()

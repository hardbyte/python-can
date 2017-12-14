import unittest
import tempfile
from time import sleep

import can

# List of messages of different types that can be used in tests
TEST_MESSAGES = [
    can.Message(
        arbitration_id=0xDADADA, extended_id=True, is_remote_frame=False,
        timestamp=1483389464.165,
        data=[1, 2, 3, 4, 5, 6, 7, 8]),
    can.Message(
        arbitration_id=0x123, extended_id=False, is_remote_frame=False,
        timestamp=1483389464.365,
        data=[254, 255]),
    can.Message(
        arbitration_id=0x768, extended_id=False, is_remote_frame=True,
        timestamp=1483389466.165),
    can.Message(is_error_frame=True, timestamp=1483389466.170),
]

def _test_writer_and_reader(test_case, writer_constructor, reader_constructor, sleep_time=0):
    """Tests a pair of writer and reader.

    The :attr:`sleep_time` specifies the time to sleep after
    writing all messages.
    """

    temp = tempfile.NamedTemporaryFile('w', delete=False)
    temp.close()
    filename = temp.name
    writer = writer_constructor(filename)

    for msg in TEST_MESSAGES:
        writer(msg)

    sleep(sleep_time)
    writer.stop()

    messages = list(reader_constructor(filename))
    test_case.assertEqual(len(messages), len(TEST_MESSAGES))
    for msg1, msg2 in zip(messages, TEST_MESSAGES):
        test_case.assertEqual(msg1, msg2)
        test_case.assertAlmostEqual(msg1.timestamp, msg2.timestamp)


class TestCanutilsLog(unittest.TestCase):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def test(self):
        _test_writer_and_reader(self, can.CanutilsLogWriter, can.CanutilsLogReader)

class TestAscFileFormat(unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def test(self):
        _test_writer_and_reader(self, can.ASCWriter, can.ASCReader)

class TestSqlFileFormat(unittest.TestCase):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def test(self):
        _test_writer_and_reader(self, can.SqliteWriter, can.SqlReader, sleep_time=0.25)


if __name__ == '__main__':
    unittest.main()

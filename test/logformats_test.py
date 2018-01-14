import unittest
import tempfile
from time import sleep

import can

TIME = 1483389946.197 # some random number

# List of messages of different types that can be used in tests
TEST_MESSAGES = [
    can.Message(
        # empty
    ),
    can.Message(
        # only data
        data=[0x00, 0x42]
    ),
    can.Message(
        # no data
        arbitration_id=0xAB, extended_id=False
    ),
    can.Message(
        # no data
        arbitration_id=0x42, extended_id=True
    ),
    can.Message(
        # empty data
        data=[]
    ),
    can.Message(
        arbitration_id=0xDADADA, extended_id=True, is_remote_frame=False,
        timestamp=TIME + .165,
        data=[1, 2, 3, 4, 5, 6, 7, 8]
    ),
    can.Message(
        arbitration_id=0x123, extended_id=False, is_remote_frame=False,
        timestamp=TIME + .365,
        data=[254, 255]
    ),
    can.Message(
        arbitration_id=0x768, extended_id=False, is_remote_frame=True,
        timestamp=TIME + 3.165
    ),
    can.Message(
        is_error_frame=True,
        timestamp=TIME + 0.170
    ),
    can.Message(
        arbitration_id=0xABCDEF, extended_id=True,
        timestamp=TIME,
        data=[1, 2, 3, 4, 5, 6, 7, 8]
    ),
    can.Message(
        arbitration_id=0x123, extended_id=False,
        timestamp=TIME + 42.42,
        data=[0xff, 0xff]
    ),
    can.Message(
        arbitration_id=0xABCDEF, extended_id=True, is_remote_frame=True,
        timestamp=TIME + 7858.67
    )
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

    for i, (read, original) in enumerate(zip(messages, TEST_MESSAGES)):
        try:
            test_case.assertEqual(read, original)
            test_case.assertAlmostEqual(read.timestamp, original.timestamp)
        except Exception as exception:
            # attach the index
            exception.args += ("test failed at index #{}".format(i), )
            raise exception


class TestCanutilsLog(unittest.TestCase):
    """Tests can.CanutilsLogWriter and can.CanutilsLogReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.CanutilsLogWriter, can.CanutilsLogReader)

class TestAscFileFormat(unittest.TestCase):
    """Tests can.ASCWriter and can.ASCReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.ASCWriter, can.ASCReader)

class TestSqlFileFormat(unittest.TestCase):
    """Tests can.SqliteWriter and can.SqliteReader"""

    def test_writer_and_reader(self):
        _test_writer_and_reader(self, can.SqliteWriter, can.SqlReader, sleep_time=0.5)


if __name__ == '__main__':
    unittest.main()

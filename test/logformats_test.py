import unittest
import tempfile
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


class TestCanutilsLog(unittest.TestCase):

    def test_reader_writer(self):
        f = tempfile.NamedTemporaryFile('w', delete=False)
        f.close()
        filename = f.name
        writer = can.CanutilsLogWriter(filename)

        for msg in TEST_MESSAGES:
            writer(msg)
        writer.stop()

        messages = list(can.CanutilsLogReader(filename))
        self.assertEqual(len(messages), len(TEST_MESSAGES))
        for msg1, msg2 in zip(messages, TEST_MESSAGES):
            self.assertEqual(msg1, msg2)
            self.assertAlmostEqual(msg1.timestamp, msg2.timestamp)

class TestAscFileFormat(unittest.TestCase):

    def test_reader_writer(self):
        f = tempfile.NamedTemporaryFile('w', delete=False)
        f.close()
        filename = f.name

        writer = can.ASCWriter(filename)
        for msg in TEST_MESSAGES:
            writer(msg)
        writer.stop()

        messages = list(can.ASCReader(filename))
        self.assertEqual(len(messages), len(TEST_MESSAGES))
        for msg1, msg2 in zip(messages, TEST_MESSAGES):
            self.assertEqual(msg1, msg2)
            self.assertAlmostEqual(msg1.timestamp, msg2.timestamp)

if __name__ == '__main__':
    unittest.main()


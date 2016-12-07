from time import sleep
import unittest
import random
import logging
import tempfile

import can

channel = 'vcan0'
can.rc['interface'] = 'virtual'

logging.getLogger("").setLevel(logging.DEBUG)


def generate_message(arbitration_id):
    data = [random.randrange(0, 2 ** 8 - 1) for b in range(8)]
    m = can.Message(arbitration_id=arbitration_id, data=data, extended_id=False)
    return m


class ListenerImportTest(unittest.TestCase):

    def testClassesImportable(self):
        assert hasattr(can, 'Listener')
        assert hasattr(can, 'BufferedReader')
        assert hasattr(can, 'Notifier')
        assert hasattr(can, 'ASCWriter')
        assert hasattr(can, 'SqlReader')


class BusTest(unittest.TestCase):

    def setUp(self):
        self.bus = can.interface.Bus()

    def tearDown(self):
        self.bus.shutdown()


class ListenerTest(BusTest):

    def testBasicListenerCanBeAddedToNotifier(self):
        a_listener = can.Listener()
        notifier = can.Notifier(self.bus, [a_listener], 0.1)
        notifier.stop()
        self.assertIn(a_listener, notifier.listeners)

    def testLogger(self):
        def test_filetype_to_instance(extension, klass):
            can_logger = can.Logger("test.{}".format(extension))
            self.assertIsInstance(can_logger, klass)
            can_logger.stop()

        test_filetype_to_instance('asc', can.ASCWriter)
        test_filetype_to_instance("csv", can.CSVWriter)
        test_filetype_to_instance("db", can.SqliteWriter)
        test_filetype_to_instance("txt", can.Printer)

    def testBufferedListenerReceives(self):
        a_listener = can.BufferedReader()
        a_listener(generate_message(0xDADADA))
        m = a_listener.get_message(0.2)
        self.assertIsNotNone(m)

    def testSQLWriterReceives(self):
        f = tempfile.NamedTemporaryFile('w')
        a_listener = can.SqliteWriter(f.name)
        a_listener(generate_message(0xDADADA))
        # Small delay so we don't stop before we actually block trying to read
        sleep(0.5)
        a_listener.stop()

        import sqlite3
        con = sqlite3.connect(f.name)
        c = con.cursor()
        c.execute("select * from messages")
        msg = c.fetchone()
        con.close()
        assert msg[1] == 0xDADADA


    def testSQLWriterWritesToSameFile(self):
        f = tempfile.NamedTemporaryFile('w')

        first_listener = can.SqliteWriter(f.name)
        first_listener(generate_message(0x01))

        sleep(1.0)
        first_listener.stop()

        second_listener = can.SqliteWriter(f.name)
        second_listener(generate_message(0x02))

        sleep(1.0)
        second_listener.stop()

        import sqlite3
        con = sqlite3.connect(f.name)

        with con:
            c = con.cursor()

            c.execute("select COUNT() from messages")
            self.assertEqual(2, c.fetchone()[0])

            c.execute("select * from messages")
            msg1 = c.fetchone()
            msg2 = c.fetchone()

        assert msg1[1] == 0x01
        assert msg2[1] == 0x02


    def testAscListener(self):
        a_listener = can.ASCWriter("test.asc", channel=2)
        a_listener.log_event("This is some comment")
        msg = can.Message(extended_id=True,
                          timestamp=a_listener.started + 0.5,
                          arbitration_id=0xabcdef,
                          data=[1, 2, 3, 4, 5, 6, 7, 8])
        a_listener(msg)
        msg = can.Message(extended_id=False,
                          timestamp=a_listener.started + 1,
                          arbitration_id=0x123,
                          data=[0xff, 0xff])
        a_listener(msg)
        msg = can.Message(extended_id=True,
                          timestamp=a_listener.started + 1.5,
                          is_remote_frame=True,
                          dlc=8,
                          arbitration_id=0xabcdef)
        a_listener(msg)
        msg = can.Message(is_error_frame=True,
                          timestamp=a_listener.started + 1.6,
                          arbitration_id=0xabcdef)
        a_listener(msg)
        a_listener.stop()
        with open("test.asc", "r") as f:
            print("Output from ASCWriter:")
            print(f.read())


class FileReaderTest(BusTest):

    def test_sql_reader(self):
        f = tempfile.NamedTemporaryFile('w')
        a_listener = can.SqliteWriter(f.name)
        a_listener(generate_message(0xDADADA))
        sleep(0.5)
        a_listener.stop()

        reader = can.SqlReader(f.name)

        ms = []
        for m in reader:
            ms.append(m)

        self.assertEqual(len(ms), 1)
        self.assertEqual(0xDADADA, ms[0].arbitration_id)

if __name__ == '__main__':
    unittest.main()

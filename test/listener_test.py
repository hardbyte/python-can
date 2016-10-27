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


class ListenerTest(unittest.TestCase):

    def setUp(self):
        self.bus = can.interface.Bus()

    def tearDown(self):
        self.bus.shutdown()

    def testBasicListenerCanBeAddedToNotifier(self):
        a_listener = can.Listener()
        notifier = can.Notifier(self.bus, [a_listener], 0.1)
        notifier.stop()
        self.assertIn(a_listener, notifier.listeners)

    def testLogger(self):
        self.assertIsInstance(can.Logger("test.asc"), can.ASCWriter)
        self.assertIsInstance(can.Logger("test.csv"), can.CSVWriter)
        self.assertIsInstance(can.Logger("test.db"), can.SqliteWriter)
        self.assertIsInstance(can.Logger("test.txt"), can.Printer)

    def testBufferedListenerReceives(self):
        a_listener = can.BufferedReader()
        a_listener(generate_message(0xDADADA))
        m = a_listener.get_message(0.2)
        self.assertIsNotNone(m)

    def testSQLWriterReceives(self):
        f = tempfile.NamedTemporaryFile('w')
        a_listener = can.SqliteWriter(f.name)
        a_listener(generate_message(0xDADADA))
        a_listener.stop()

        import sqlite3
        con = sqlite3.connect(f.name)
        c = con.cursor()
        c.execute("select * from messages")
        msg = c.fetchone()
        assert msg[1] == 0xDADADA

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
        a_listener.stop()
        with open("test.asc") as f:
            print("Output from ASCWriter:")
            print(f.read())


if __name__ == '__main__':
    unittest.main()

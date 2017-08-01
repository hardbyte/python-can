# -*- coding: utf-8 -*-

import unittest
import threading
import time
import platform
import can
from can.interfaces.remote import client
import logging

logging.basicConfig(level=logging.DEBUG)


def raise_error(msg):
    raise can.CanError('This is some error')


#@unittest.skip('Take a lot of time')
class RemoteBusTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        server = can.interfaces.remote.RemoteServer(
            '127.0.0.1', 54700, channel='unittest', bustype='virtual')
        server_thread = threading.Thread(target=server.serve_forever, name='Server thread')
        server_thread.daemon = True
        server_thread.start()
        cls.server = server
        # Wait for server to be properly started
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        # Connect to remote bus on localhost
        self.remote_bus = can.interface.Bus('ws://127.0.0.1:54700/',
                                            bustype='remote',
                                            bitrate=125000)
        # Connect to real bus directly
        self.real_bus = can.interface.Bus('unittest', bustype='virtual')
        # Wait some time so that self.server.clients is updated
        time.sleep(0.1)

    def tearDown(self):
        self.real_bus.shutdown()
        self.remote_bus.shutdown()

    def test_initialization(self):
        self.assertEqual(self.remote_bus.channel_info,
                         '%s on ws://127.0.0.1:54700/' % self.real_bus.channel_info)
        self.assertEqual(self.server.clients[-1].config["bitrate"], 125000)

        # Test to create a new bus with filters
        can_filters = [
            {'can_id': 0x12, 'can_mask': 0xFF, 'extended': False},
            {'can_id': 0x13, 'can_mask': 0xFF, 'extended': True}
        ]
        bus = can.interface.Bus('127.0.0.1:54700',
                                bustype='remote',
                                bitrate=1000000,
                                can_filters=can_filters)
        # Wait some time so that self.server.clients is updated
        time.sleep(0.1)
        self.assertEqual(self.server.clients[-1].config["can_filters"], can_filters)
        self.assertEqual(self.server.clients[-1].config["bitrate"], 1000000)
        bus.shutdown()

    def test_send(self):
        std_msg = can.Message(arbitration_id=0x100, extended_id=False,
                              data=[1, 2, 3, 4])
        ext_msg = can.Message(arbitration_id=0xabcdef, extended_id=True,
                           data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff])
        self.remote_bus.send(std_msg)
        self.remote_bus.send(ext_msg)
        msg1_on_remote = self.real_bus.recv(5)
        msg2_on_remote = self.real_bus.recv(5)
        self.assertEqual(msg1_on_remote, std_msg)
        self.assertEqual(msg2_on_remote, ext_msg)

    # For some reason this test fails intermittently on PyPy
    # Sometimes the messages come in some random order or something
    @unittest.skipIf(platform.python_implementation() == "PyPy", "PyPy not supported")
    def test_recv(self):
        msg = can.Message(arbitration_id=0x123, data=[8, 7, 6, 5, 4, 3, 2, 1])
        empty_msg = can.Message()
        self.real_bus.send(msg)
        self.real_bus.send(empty_msg)
        first_received = self.remote_bus.recv(1)
        second_received = self.remote_bus.recv(1)
        third_received = self.remote_bus.recv(0.1)
        self.assertIsNotNone(first_received)
        self.assertEqual(first_received, msg)
        self.assertIsNotNone(second_received)
        self.assertEqual(second_received, empty_msg)
        self.assertIsNone(third_received)

    def test_recv_failure(self):
        self.server.clients[-1].bus.recv = raise_error
        with self.assertRaisesRegexp(can.CanError, 'This is some error'):
            self.remote_bus.recv(5)

    def test_cyclic(self):
        test_msg = can.Message(arbitration_id=0xabcdef,
                               data=[1, 2, 3, 4, 5, 6, 7, 8])
        task = self.remote_bus.send_periodic(test_msg, 0.01)
        time.sleep(2)
        task.stop()
        msgs = []
        msg = self.real_bus.recv(0)
        while msg is not None:
            msgs.append(msg)
            msg = self.real_bus.recv(0)
        self.assertTrue(150 < len(msgs) < 220)
        self.assertEqual(msgs[0], test_msg)


if __name__ == '__main__':
    unittest.main()

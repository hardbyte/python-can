# -*- coding: utf-8 -*-

import unittest
import threading
import time
import can
from can.interfaces.remote import events
from can.interfaces.remote import connection
import logging

logging.basicConfig(level=logging.DEBUG)


def raise_error(msg):
    raise can.CanError('This is some error')


class EventsTestCase(unittest.TestCase):

    def test_message(self):
        messages = [
            can.Message(timestamp=1470925506.0621243,
                        arbitration_id=0x100,
                        extended_id=False,
                        data=[1, 2, 3, 4]),
            can.Message(arbitration_id=0xabcdef,
                        extended_id=True,
                        data=[0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff]),
            can.Message(),
            can.Message(is_error_frame=True),
            can.Message(is_remote_frame=True,
                        arbitration_id=0x123)
        ]

        for msg in messages:
            send_event = events.CanMessage(msg)
            buf = send_event.encode()
            recv_event = events.CanMessage.from_buffer(buf)
            self.assertEqual(recv_event, send_event)
            self.assertAlmostEqual(recv_event.msg.timestamp, msg.timestamp)
            self.assertEqual(len(recv_event), len(buf))

    def test_bus_request(self):
        event1 = events.BusRequest(12, 1000000)
        buf = event1.encode()
        event2 = events.BusRequest.from_buffer(buf)
        self.assertEqual(event1, event2)
        self.assertEqual(len(event2), len(buf))

    def test_filter_config(self):
        event1 = events.FilterConfig([
            {'can_id': 0x1FFFFFFF, 'can_mask': 0x1FFFFFFF, 'extended': True},
            {'can_id': 0x001, 'can_mask': 0x00F, 'extended': False}
        ])
        buf = event1.encode()
        event2 = events.FilterConfig.from_buffer(buf)
        self.assertEqual(event1, event2)
        self.assertEqual(len(event2), len(buf))

        event1 = events.FilterConfig([])
        buf = event1.encode()
        event2 = events.FilterConfig.from_buffer(buf)
        self.assertEqual(event1, event2)
        self.assertEqual(len(event2), len(buf))

    def test_bus_response(self):
        channel_info = 'This is some channel info'
        event1 = events.BusResponse(channel_info)
        buf = event1.encode()
        event2 = events.BusResponse.from_buffer(buf)
        self.assertEqual(event1, event2)
        self.assertEqual(len(event2), len(buf))

    def test_exception(self):
        event1 = events.RemoteException(can.CanError('This is an error'))
        buf = event1.encode()
        event2 = events.RemoteException.from_buffer(buf)
        self.assertEqual(str(event1.exc), str(event2.exc))
        self.assertEqual(len(event2), len(buf))

    def test_periodic_start(self):
        msg = can.Message(0x123,
                          extended_id=False,
                          data=[1, 2, 3, 4, 5, 6, 7, 8])
        event1 = events.PeriodicMessageStart(msg, 0.01, 10)
        buf = event1.encode()
        event2 = events.PeriodicMessageStart.from_buffer(buf)
        self.assertEqual(event1, event2)
        self.assertAlmostEqual(event1.period, event2.period)
        self.assertAlmostEqual(event1.duration, event2.duration)
        self.assertEqual(len(event2), len(buf))


class ConnectionTestCase(unittest.TestCase):

    def setUp(self):
        self.sender = connection.Connection()
        self.receiver = connection.Connection()

    def test_send_and_receive(self):
        event1 = events.CanMessage(can.Message())
        self.sender.send_event(event1)
        self.receiver.receive_data(self.sender.next_data())
        event2 = self.receiver.next_event()
        self.assertEqual(event1, event2)

        # No more events shall be returned
        self.assertIsNone(self.receiver.next_event())

    def test_empty_events(self):
        self.sender.send_event(events.TransmitSuccess())
        self.receiver.receive_data(self.sender.next_data())
        event = self.receiver.next_event()
        self.assertIsInstance(event, events.TransmitSuccess)

    def test_partial_transfer(self):
        event1 = events.CanMessage(can.Message())
        self.sender.send_event(event1)
        data = self.sender.next_data()

        # Send only first 8 bytes
        self.receiver.receive_data(data[:8])
        self.assertIsNone(self.receiver.next_event())

        # Send the rest (and some more)
        self.receiver.receive_data(data[8:])
        self.receiver.receive_data(b'hello')
        event2 = self.receiver.next_event()
        self.assertEqual(event1, event2)

    def test_iteration(self):
        event1 = events.CanMessage(can.Message())
        self.sender.send_event(event1)
        data = self.sender.next_data()
        self.receiver.receive_data(data * 8)

        self.assertListEqual(list(self.receiver), [event1] * 8)

    def test_invalid_event(self):
        self.receiver.receive_data(b'\xf0')
        with self.assertRaises(connection.ProtocolError):
            self.receiver.next_event()

    def test_close(self):
        self.assertFalse(self.receiver.closed)
        self.receiver.receive_data(b'')
        event = self.receiver.next_event()
        self.assertTrue(self.receiver.closed)
        self.assertIsInstance(event, events.ConnectionClosed)


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
        self.remote_bus = can.interface.Bus('127.0.0.1:54700',
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
                         '%s on 127.0.0.1:54700' % self.real_bus.channel_info)
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

    def test_recv(self):
        msg = can.Message(arbitration_id=0x123, data=[8, 7, 6, 5, 4, 3, 2, 1])
        empty_msg = can.Message()
        self.real_bus.send(msg)
        self.real_bus.send(empty_msg)
        first_received = self.remote_bus.recv(0.1)
        second_received = self.remote_bus.recv(0.1)
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
            msg = self.real_bus.recv(0)
            if msg is not None:
                msgs.append(msg)
        self.assertTrue(150 < len(msgs) < 220)
        self.assertEqual(msgs[0], test_msg)


if __name__ == '__main__':
    unittest.main()

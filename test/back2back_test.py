import unittest

import can


BITRATE = 500000
TIMEOUT = 0.1

INTERFACE_1 = 'virtual'
CHANNEL_1 = 0
INTERFACE_2 = 'virtual'
CHANNEL_2 = 0


class Back2BackTestCase(unittest.TestCase):
    """
    Use two interfaces connected to the same CAN bus and test them against
    each other.
    """

    def setUp(self):
        self.bus1 = can.interface.Bus(channel=CHANNEL_1,
                                      bustype=INTERFACE_1,
                                      bitrate=BITRATE)
        self.bus2 = can.interface.Bus(channel=CHANNEL_2,
                                      bustype=INTERFACE_2,
                                      bitrate=BITRATE)

    def tearDown(self):
        self.bus1.shutdown()
        self.bus2.shutdown()

    def _send_and_receive(self, msg):
        # Send with bus 1, receive with bus 2
        self.bus1.send(msg)
        recv_msg = self.bus2.recv(TIMEOUT)
        self.assertIsNotNone(recv_msg,
                             "No message was received on %s" % INTERFACE_2)
        self.assertEqual(recv_msg, msg)

        # Send with bus 2, receive with bus 1
        # Add 1 to arbitration ID to make it a different message
        msg.arbitration_id += 1
        self.bus2.send(msg)
        recv_msg = self.bus1.recv(TIMEOUT)
        self.assertIsNotNone(recv_msg,
                             "No message was received on %s" % INTERFACE_1)
        self.assertEqual(recv_msg, msg)

    def test_standard_message(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x100,
                          data=[1, 2, 3, 4, 5, 6, 7, 8])
        self._send_and_receive(msg)

    def test_extended_message(self):
        msg = can.Message(extended_id=True,
                          arbitration_id=0x123456,
                          data=[10, 11, 12, 13, 14, 15, 16, 17])
        self._send_and_receive(msg)

    def test_remote_message(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x200,
                          is_remote_frame=True,
                          dlc=4)
        self._send_and_receive(msg)

    def test_dlc_less_than_eight(self):
        msg = can.Message(extended_id=False,
                          arbitration_id=0x300,
                          data=[4, 5, 6])
        self._send_and_receive(msg)


if __name__ == '__main__':
    unittest.main()

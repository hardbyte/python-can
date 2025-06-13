#!/usr/bin/env python3
# coding: utf-8

import unittest
import time
import can

from can.exceptions import *


class ZlgTestCase(unittest.TestCase):
    def setUp(self):
        self.channel = 0
        self.device = 0
        self.std_id = 0x123
        self.ext_id = 0x123456
        self.bitrate = 500_000
        self.data_bitrate = 2_000_000
        self.bus = can.Bus(
            bustype="zlg",
            channel=self.channel,
            device=self.device,
            bitrate=self.bitrate,
            data_bitrate=self.data_bitrate,
        )
        self.can_std_msg = can.Message(
            arbitration_id=self.std_id,
            is_extended_id=False,
            is_fd=False,
            data=list(range(8)),
        )
        self.can_ext_msg = can.Message(
            arbitration_id=self.ext_id,
            is_extended_id=True,
            is_fd=False,
            data=list(range(8)),
        )
        self.canfd_std_msg = can.Message(
            arbitration_id=self.std_id,
            is_extended_id=False,
            is_fd=True,
            data=list(range(64)),
        )
        self.canfd_ext_msg = can.Message(
            arbitration_id=self.ext_id,
            is_extended_id=True,
            is_fd=True,
            data=list(range(64)),
        )

    def tearDown(self):
        self.bus.shutdown()

    def testSendStdMsg(self):
        try:
            self.bus.send(self.can_std_msg)
        except CanOperationError as ex:
            self.fail("Failed to send CAN std frame")

    def testSendExtMsg(self):
        try:
            self.bus.send(self.can_ext_msg)
        except CanOperationError as ex:
            self.fail("Failed to send CAN ext frame")

    def testSendStdMsgFD(self):
        try:
            self.bus.send(self.canfd_std_msg)
        except CanOperationError as ex:
            self.fail("Failed to send CANFD std frame")

    def testSendExtMsgFD(self):
        try:
            self.bus.send(self.canfd_ext_msg)
        except CanOperationError as ex:
            self.fail("Failed to send CANFD ext frame")

    def testSendTimeout0S(self):
        try:
            timeout = 0
            print(f"Set send {timeout=}")
            t1 = time.time()
            self.bus.send(self.can_std_msg, timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=10)
        except Exception as ex:
            self.fail(str(ex))

    def testSendTimeout1S(self):
        try:
            timeout = 1
            print(f"Set send {timeout=}")
            t1 = time.time()
            self.bus.send(self.can_std_msg, timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=timeout * 1.1)
        except Exception as ex:
            self.fail(str(ex))

    def testSendTimeout5S(self):
        try:
            timeout = 5
            print(f"Set send {timeout=}")
            t1 = time.time()
            self.bus.send(self.can_std_msg, timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=timeout * 1.1)
        except Exception as ex:
            self.fail(str(ex))

    def testSendTimeoutForever(self):
        try:
            timeout = None
            print(f"Set send {timeout=}")
            self.bus.send(self.can_std_msg, timeout)
        except Exception as ex:
            self.fail(str(ex))

    def testRecv(self):
        msg = self.bus.recv(0)
        self.assertIsNotNone(msg)

    def testRecvTimeout0S(self):
        try:
            timeout = 0
            print(f"Set receive {timeout=}")
            t1 = time.time()
            msg = self.bus.recv(timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=10)
        except Exception as ex:
            self.fail(str(ex))

    def testRecvTimeout1S(self):
        try:
            timeout = 1
            print(f"Set receive {timeout=}")
            t1 = time.time()
            msg = self.bus.recv(timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=timeout * 1.1)
        except Exception as ex:
            self.fail(str(ex))

    def testRecvTimeout5S(self):
        try:
            timeout = 5
            print(f"Set receive {timeout=}")
            t1 = time.time()
            msg = self.bus.recv(timeout)
            t2 = time.time()
            self.assertAlmostEqual(t1, t2, delta=timeout * 1.1)
        except Exception as ex:
            self.fail(str(ex))

    def testRecvTimeoutForever(self):
        try:
            timeout = None
            print(f"Set receive {timeout=}")
            msg = self.bus.recv(timeout)
        except Exception as ex:
            self.fail(str(ex))


if __name__ == "__main__":
    unittest.main()

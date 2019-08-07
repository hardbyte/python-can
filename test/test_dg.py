#!/usr/bin/python
#
# ----------------------------------------------------------------------
# pylint: disable=invalid-name
# ----------------------------------------------------------------------
#
# **********************************************************************
# Copyright (C) 2019 DG Technologies/Dearborn Group, Inc. All rights
# reserved. The copyright here does not evidence any actual or intended
# publication.
#
# File Name: test_dg.py
# Author(s): mohtake <mohtake@dgtech.com>
# Target Project: python-can
# Description:
# Notes:
# ----------------------------------------------------------------------
# Release Revision: $Rev: 73 $
# Release Date: $Date: 2019/08/05 14:26:05 $
# Revision Control Tags: $Tags: tip $
# ----------------------------------------------------------------------
# **********************************************************************
#

"""DG python-can unittest module"""

import time
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
import threading
from threading import Thread
import unittest
try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

# ----------------------------------------------------------------------
import can
from can import Message
from can.interfaces.dg.dg_gryphon_protocol import server_commands

class mockedBus():
    """ Mocked Bus for testing DG Interface"""

    def __init__(self):
        """Basic init for each test, sets up queue, mock, threads, etc."""
        self.q = Queue()
        self.threads = []
        self.events = []
        self.filters = []
        self.filtOn = False
        self.filtReply = {"GCprotocol": {"body": {"data": {"filter_handles": ["dummy"]}}}}
        self.ioctlReply = {"GCprotocol": {"body": {"data": {"ioctl_data": [0x01, 0x03, 0xFF]}}}}
        server_commands.Gryphon.__init__ = Mock(return_value=None)
        server_commands.Gryphon.__del__ = Mock(return_value=None)
        server_commands.Gryphon.CMD_SERVER_REG = Mock()
        server_commands.Gryphon.FT_DATA_TX = Mock(side_effect=self.add_queue)
        server_commands.Gryphon.CMD_BCAST_ON = Mock()
        server_commands.Gryphon.CMD_CARD_IOCTL = Mock(return_value=self.ioctlReply)
        server_commands.Gryphon.CMD_INIT = Mock()
        server_commands.Gryphon.CMD_SCHED_TX = Mock(side_effect=self.send_sched)
        server_commands.Gryphon.FT_DATA_WAIT_FOR_RX = Mock(side_effect=self.get_queue)
        server_commands.Gryphon.CMD_CARD_GET_FILTER_HANDLES = Mock(return_value=self.filtReply)
        server_commands.Gryphon.CMD_CARD_MODIFY_FILTER = Mock()
        server_commands.Gryphon.CMD_CARD_SET_DEFAULT_FILTER = Mock(side_effect=self.del_filt)
        server_commands.Gryphon.CMD_CARD_ADD_FILTER = Mock(side_effect=self.set_filt)
        server_commands.Gryphon.CMD_CARD_SET_FILTER_MODE = Mock(side_effect=self.filt_mode)
        server_commands.Gryphon.CMD_SCHED_MSG_REPLACE = Mock(side_effect=self.change_sched)
        server_commands.Gryphon.CMD_SCHED_KILL_TX = Mock(side_effect=self.kill_sched)

    def filt_mode(self, *args):
        """Set the filter mode to on or off"""
        if args[1] == 5:
            self.filtOn = True
        else:
            self.filtOn = False

    def del_filt(self, *args):
        """Delete a filter if SET_DEFAULT_FILTER is called"""
        if args[1] == 1:
            self.filters = []
            self.filtOn = False

    def set_filt(self, *args):
        """Setup a filter"""
        filts = args[1]["filter_blocks"]
        for i in range(0, len(filts)):
            self.filters.append(filts[i]["pattern"])

    def filt_check(self, hdr):
        """Make filter check before sending to queue"""
        if hdr in self.filters:
            return True
        return False

    def add_queue(self, *args):
        """Add a message to the message queue"""
        if not self.filtOn or self.filt_check(args[1]["hdr"]):
            self.q.put(args[1])

    def get_queue(self, **kwargs):
        """Get a message from the message queue, if there are any"""
        try:
            x = self.q.get(timeout=kwargs["timeout"])
        except:
            return None
        rxReply = {"GCprotocol": {"body": {"data": x}}}
        rxReply["GCprotocol"]["body"]["data"]["timestamp"] = 100000
        rxReply["GCprotocol"]["body"]["data"]["status"] = 20
        return rxReply

    def send_msg_thread(self, msg, wait, iterations, tEv):
        """Thread for sending a periodic message"""
        wait = wait / 1000000.0
        if tEv is not None:
            while not tEv.is_set():
                self.add_queue(None, msg)
                time.sleep(wait)
        else:
            for _ in range(0, iterations):
                self.add_queue(None, msg)
                time.sleep(wait)

    def send_sched(self, *args, **kwargs):
        """Setup up the scheduler message"""
        txMsg = args[1]["message_list"][0]
        wait = txMsg["tx_period"]
        txMsg.pop("tx_period")
        txMsg.pop("period_in_microsec")
        tEv = threading.Event()
        t = Thread(target=self.send_msg_thread, args=(txMsg, wait, kwargs["iterations"], tEv))
        t.daemon = True
        self.threads.append(t)
        self.events.append(tEv)
        t.start()
        return {"schedule_id" : len(self.threads)}

    def change_sched(self):
        """Not currently implemented"""
        raise NotImplementedError

    def kill_sched(self, *args):
        """Kill a schedule and wait for join"""
        self.events[args[1] - 1].set()
        self.threads[args[1] -1].join()


class test_dg(unittest.TestCase):
    """ Tests dg interface"""

    def setUp(self):
        """Setup mockedBus for each test"""
        mockedBus()

    def test_filter_schedule(self):
        """
        REQUIRES: shutdown, task.stop_all_periodic_tasks
        TESTS: _apply_filters(filter), _send_periodic_internal()
        """
        print("\ntest_filter_schedule")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[12, 255, 29, 152])
            bus.send_periodic(msg, .1)
            filt = [{"can_id": 0x054a, "can_mask": 0xffff, "extended": True}]
            time.sleep(1)
            bus.set_filters(filt)
            for _ in range(0, 50):
                bus.recv(timeout=0)
            time.sleep(1)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_RX_TX(self):
        """
        REQUIRES: shutdown
        TESTS: _recv_internal, send
        """
        print("\ntest_RX_TX")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[12, 255, 29, 152])
            bus.send(msg)
            reply = bus.recv()
            self.assertEqual(reply.arbitration_id, 0x05ea)
            self.assertEqual(reply.data, bytearray([12, 255, 29, 152]))
        finally:
            bus.shutdown()

    def test_configs(self):
        """
        REQUIRES: shutdown
        TESTS: _detect_available_configs
        """
        print("\ntest_configs")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            conf = bus._detect_available_configs()
            for item in conf:
                self.assertTrue(isinstance(item["chan"], int))
        finally:
            bus.shutdown()

    def test_flush(self):
        """
        REQUIRES: shutdown
        TESTS: flush_tx_buffer
        """
        print("\ntest_flush")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            bus.flush_tx_buffer()
            self.assertTrue(True)
        finally:
            bus.shutdown()

    def test_filter_simple(self):
        """
        REQUIRES: shutdown, _recv_internal, send
        TESTS: _apply_filters(filt)
        """
        print("\ntest_filter_simple")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[12, 255, 29, 152])
            filt = [{"can_id": 0x054a, "can_mask": 0xffff, "extended": True}]
            bus.set_filters(filters=filt)
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(None, reply)
        finally:
            bus.shutdown()

    def test_filter_shutoff(self):
        """
        REQUIRES: shutdown, _recv_internal, send, _apply_filters(filt)
        TESTS: _apply_filters()
        """
        print("\ntest_filter_shutoff")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x01ef, data=[12, 255, 29, 152])
            filt = [{"can_id": 0x054a, "can_mask": 0xffff, "extended": True}]
            bus.set_filters(filters=filt)
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(None, reply)
            bus.set_filters()
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x01ef)
        finally:
            bus.shutdown()

    def test_long_filter(self):
        """
        REQUIRES: shutdown, _recv_internal, send
        TESTS: _apply_filters(filt)
        """
        print("\ntest_long_filter")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x0132, data=[12, 255, 29, 152])
            filt = [{"can_id": 0x01e00132, "can_mask": 0xffffffff, "extended": True}]
            bus.set_filters(filters=filt)
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(None, reply)
            msg.arbitration_id = 0x01e00132
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x01e00132)
            msg.arbitration_id = 0x01e0a132
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply, None)
            time.sleep(.5)
            # Above is needed so filter doesn't mess with other tests
        finally:
            bus.shutdown()

    def test_add_and_clear_filter(self):
        """
        REQUIRES: shutdown, _recv_internal, send
        TESTS: _apply_filters(filt), _apply_filters()
        """
        print("\ntest_add_and_clear_filter")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x01e2, data=[12, 255, 29, 182])
            msg2 = Message(arbitration_id=0x01e00132, data=[12, 255, 29, 152])
            msg3 = Message(arbitration_id=0x04ea, data=[12, 255, 29, 152])
            filt = [{"can_id": 0x01e00132, "can_mask": 0xffffffff, "extended": True}]
            bus.set_filters(filters=filt)
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply, None)
            filt2 = [{"can_id": 0x01e2, "can_mask": 0xffff}]
            bus.set_filters(filters=filt2)
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x01e2)
            bus.send(msg2)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x01e00132)
            bus.set_filters()
            bus.send(msg3)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x04ea)
        finally:
            bus.shutdown()

    def test_simple_sched(self):
        """
        REQUIRES: shutdown, _recv_internal
        TESTS: _send_periodic_internal(), task.stop
        """
        print("\ntest_simple_sched")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x01e2, data=[12, 255, 29, 252])
            task = bus.send_periodic(msg, .5)
            time.sleep(2.2)
            task.stop()
            for _ in range(0, 4):
                reply = bus.recv(timeout=0)
                self.assertEqual(reply.arbitration_id, 0x01e2)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_sched_accuracy(self):
        """
        REQUIRES: shutdown, _recv_internal
        TESTS: _send_periodic_internal(), task.stop
        """
        print("\ntest_sched_accuracy")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x01e2, data=[12, 255, 29, 140])
            task = bus.send_periodic(msg, .2)
            time.sleep(3.1)
            task.stop()
            for _ in range(0, 16):
                reply = bus.recv(timeout=0)
                self.assertEqual(reply.arbitration_id, 0x01e2)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    # Not going to bother with modifying schedules at the moment
    def _test_alter_sched(self):
        """
        REQUIRES: shutdown, _recv_internal, _send_periodic_internal(), task.stop
        TESTS: task.modify_data
        """
        print("\ntest_alter_sched")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x01e2, data=[12, 255, 29, 160])
            task = bus.send_periodic(msg, .5)
            time.sleep(3.2)
            msg.data = [34, 13, 22, 1]
            task.modify_data(msg)
            time.sleep(3.2)
            task.stop()
            for _ in range(0, 7):
                reply = bus.recv(timeout=0)
                self.assertEqual(reply.arbitration_id, 0x01e2)
            for _ in range(0, 6):
                reply = bus.recv(timeout=0)
                self.assertEqual(reply.data, bytearray([34, 13, 22, 1]))
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_mult_sched(self):
        """
        REQUIRES: shutdown, _recv_internal
        TESTS: _send_periodic_internal(duration)
        """
        print("\ntest_mult_sched")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg1 = Message(arbitration_id=0x01ee, data=[12, 255])
            msg2 = Message(arbitration_id=0x043ea209, data=[16, 211, 15])
            bus.send_periodic(msg1, .5, 3.2)
            time.sleep(.25)
            bus.send_periodic(msg2, .5, 3.2)
            for _ in range(0, 6):
                reply = bus.recv(timeout=.6)
                self.assertEqual(reply.arbitration_id, 0x01ee)
                reply = bus.recv(timeout=.6)
                self.assertEqual(reply.arbitration_id, 0x043ea209)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.shutdown()

    def test_stop_all_tasks(self):
        """
        REQUIRES: shutdown, _recv_internal
        TESTS: stop_all_periodic_tasks
        """
        print("\ntest_stop_all_tasks")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg1 = Message(arbitration_id=0x01ff4332, data=[12, 255, 29, 152])
            msg2 = Message(arbitration_id=0x043ea209, data=[16, 211])
            msg3 = Message(arbitration_id=0x02090001, data=[16, 211, 15, 22])
            msg5 = Message(arbitration_id=0x0401, data=[16, 211, 15, 22])
            bus.send_periodic(msg1, .5, 3, store_task=True)
            bus.send_periodic(msg2, .4, 6, store_task=True)
            bus.send_periodic(msg3, .1, 4, store_task=True)
            bus.send_periodic(msg5, .1, 4, store_task=True)
            bus.stop_all_periodic_tasks(remove_tasks=False)
            time.sleep(1)
            for _ in range(1, 50):
                bus.recv(timeout=0)
            time.sleep(1)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_TS_RX_TX(self):
        """
        THREAD-SAFE
        REQUIRES: shutdown
        TESTS: send, _recv_internal
        """
        print("\ntest_TS_RX_TX")
        bus = can.ThreadSafeBus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[122, 122, 122, 122])
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x05ea)
            self.assertEqual(reply.data, bytearray([122, 122, 122, 122]))
        finally:
            bus.shutdown()

    def test_CANFD_RX_TX(self):
        """
        REQUIRES: shutdown
        TESTS: send, _recv_internal
        """
        print("\ntest_CANFD_RX_TX")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CANFD", ip="10.93.172.9")
        bus2 = can.interface.Bus(bustype="dg", chan=2, mode="CANFD", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[122, 122, 122, 122])
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x05ea)
            self.assertEqual(reply.data, bytearray([122, 122, 122, 122]))
        finally:
            bus.shutdown()
            bus2.shutdown()

    def test_PREISO_RX_TX(self):
        """
        REQUIRES: shutdown
        TESTS: send, _recv_internal
        """
        print("\ntest_PREISO_RX_TX")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CANPREISO", ip="10.93.172.9")
        bus2 = can.interface.Bus(bustype="dg", chan=2, mode="CANPREISO", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x05ea, data=[122, 122, 122, 122])
            bus.send(msg)
            reply = bus.recv(timeout=1)
            self.assertEqual(reply.arbitration_id, 0x05ea)
            self.assertEqual(reply.data, bytearray([122, 122, 122, 122]))
        finally:
            bus.shutdown()
            bus2.shutdown()

    def test_TS_stop_all_tasks(self):
        """
        THREAD-SAFE
        REQUIRES: shutdown, _recv_internal
        TESTS: _send_periodic_internal, _send_periodic_internal(duration)
        """
        print("\ntest_TS_stop_all_tasks")
        bus = can.ThreadSafeBus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg1 = Message(arbitration_id=0x01ff4332, data=[12, 255, 29, 152])
            msg2 = Message(arbitration_id=0x043ea209, data=[16, 211])
            msg3 = Message(arbitration_id=0x02090001, data=[16, 211, 15, 22])
            msg4 = Message(arbitration_id=0x02090001, data=[16, 211, 15, 22])
            msg5 = Message(arbitration_id=0x0401, data=[16, 211, 15, 22])
            bus.send_periodic(msg1, .5, 3, store_task=True)
            bus.send_periodic(msg2, .4, 6, store_task=True)
            bus.send_periodic(msg3, .1, store_task=True)
            bus.send_periodic(msg4, .1, 4, store_task=True)
            bus.send_periodic(msg5, .1, 4, store_task=True)
            bus.stop_all_periodic_tasks(remove_tasks=False)
            time.sleep(1)
            for _ in range(1, 50):
                bus.recv(timeout=0)
            time.sleep(1)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_TS_sched_accuracy(self):
        """
        THREAD-SAFE
        REQUIRES: shutdown, _recv_internal
        TESTS: _send_periodic_internal
        """
        print("\ntest_TS_sched_accuracy")
        bus = can.ThreadSafeBus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        try:
            msg = Message(arbitration_id=0x0444, data=[12, 255, 29, 152])
            task = bus.send_periodic(msg, .2)
            time.sleep(3.1)
            task.stop()
            for _ in range(0, 16):
                reply = bus.recv(timeout=0)
                self.assertEqual(reply.arbitration_id, 0x0444)
            reply = bus.recv(timeout=0)
            self.assertEqual(reply, None)
        finally:
            bus.stop_all_periodic_tasks(remove_tasks=False)
            bus.shutdown()

    def test_shutdown(self):
        """
        REQUIRES:
        TESTS: shutdown
        """
        print("\ntest_shutdown")
        bus = can.interface.Bus(bustype="dg", chan=1, mode="CAN", ip="10.93.172.9")
        msg = Message(arbitration_id=0x01e2, data=[12, 255, 29, 112])
        bus.shutdown()
        with self.assertRaises(AttributeError):
            bus.send(msg)


if __name__ == '__main__':
    unittest.main()

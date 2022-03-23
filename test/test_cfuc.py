#!/usr/bin/env python
# coding: utf-8

"""
This module is for CFUC testing the serial interface, UCANDevices
"""


from logging import log
import unittest
import can
from can.message import Message
# import can.interfaces.cfucBus 

class SerialDummy(object):
    """
    Dummy to mock the serial communication
    """
    msg = None

    def __init__(self):
        self.msg = bytearray()

    def read(self, size=1):
        return_value = bytearray()
        for i in range(size):
            return_value.append(self.msg.pop(0))
        return bytes(return_value)

    def write(self, msg):
        self.msg = bytearray(msg)

    def reset(self):
        self.msg = None

class CFUCTestCase(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        self.bus.shutdown()


    def test_init(self):
        """
        Tests the transfer of init frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        
        self.serial = self.bus.ser
        msg_init = self.serial.read(self.serial.in_waiting)
        self.assertIsNotNone(msg_init)


    def test_tx_frame_extended(self):
        """
        Tests the transfer of extented CAN frame
        """
        self.bus = can.Bus(
        bustype="cfuc", 
        channel="loop://", 
        CANBaudRate=100000, 
        IsFD=True, 
        FDDataBaudRate=500000, 
        )

        
        self.serial = self.bus.ser
        msg_init = self.serial.read(self.serial.in_waiting)

        msg_send = can.Message(
        arbitration_id=0xAAABBCC, 
        data=[0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 1,1],
        is_extended_id=True, 
        is_fd=True, 
        bitrate_switch=True
        )

        self.bus.send(msg_send)

        msg_recv = self.bus.recv()
        self.assertEqual(msg_recv[0].arbitration_id, msg_send.arbitration_id)
        self.assertEqual(msg_recv[0].is_extended_id, msg_send.is_extended_id)
        self.assertEqual(msg_recv[0].is_fd, msg_send.is_fd)
        self.assertEqual(msg_recv[0].data[0:2], msg_send.data[0:2])


    
    def test_tx_frame_standart(self):
        """
        Tests the transfer of standart CAN frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)

        self.serial = self.bus.ser
        msg_init = self.serial.read(self.serial.in_waiting)
        
        msg_send = can.Message(arbitration_id=0x12ABCDEF, is_extended_id=False, data=[0xAA, 0x55])
        self.bus.send(msg_send)

        msg_recv = self.bus.recv(None)
        self.assertEqual(msg_recv[0].arbitration_id, msg_send.arbitration_id)
        self.assertEqual(msg_recv[0].is_extended_id, msg_send.is_extended_id) # error
        self.assertEqual(msg_recv[0].is_fd, msg_send.is_fd)
        self.assertEqual(msg_recv[0].data[0:2], msg_send.data[0:2])
    

    def test_tx_fd_frame(self):
        """
        Tests the transfer of Flexible Data-Rate CAN frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        
        self.serial = self.bus.ser
        msg_init = self.serial.read(self.serial.in_waiting)

        msg_send = can.Message(arbitration_id=0x12ABCDEF, is_extended_id=True, is_fd = True, data=[0xAA, 0x55])
        self.bus.send(msg_send)

        msg_recv = self.bus.recv(None)
        self.assertEqual(msg_recv[0].arbitration_id, msg_send.arbitration_id)
        self.assertEqual(msg_recv[0].is_extended_id, msg_send.is_extended_id)
        self.assertEqual(msg_recv[0].is_fd, msg_send.is_fd)  # error
        self.assertEqual(msg_recv[0].data[0:2], msg_send.data[0:2])
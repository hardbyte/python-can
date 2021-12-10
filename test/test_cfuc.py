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
        msg = self.serial.read(self.serial.in_waiting)
        # msg = self.bus.recv(0)
        self.assertIsNotNone(msg)

    def test_tx_frame_extended(self):
        """
        Tests the transfer of extented CAN frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        self.serial = self.bus.ser
        self.serial.read(self.serial.in_waiting)

        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, data=[0xAA, 0x55]
        )
        self.bus.send(msg)

        data = self.serial.read(self.serial.in_waiting)
        self.assertEqual(data[11],64)  # standart / extended field 
        # self.assertIsNotNone(data)

    
    def test_tx_frame_standart(self):
        """
        Tests the transfer of extented CAN frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        self.serial = self.bus.ser
        self.serial.read(self.serial.in_waiting)

        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=False, data=[0xAA, 0x55]
        )
        self.bus.send(msg)

        data = self.serial.read(self.serial.in_waiting) 

        self.assertEqual(data[11],0)  # standart extended 
        # self.assertEqual(data[18],2)          
    
    def test_tx_fd_frame(self):
        """
        Tests the transfer of extented CAN frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        self.serial = self.bus.ser
        self.serial.read(self.serial.in_waiting)

        msg = can.Message(
            arbitration_id=0x12ABCDEF, is_extended_id=True, is_fd = True, data=[0xAA, 0x55]
        )
        self.bus.send(msg)

        data = self.serial.read(self.serial.in_waiting)
        self.assertIsNotNone(data)
                                                                                   #len           #ErrorState    #BitRateSwitch     #FDFormat
#        b'\x02\x00\x00\x00\xef\xcd\xab\x12\x00\x00\x00@\x00 \x00\x00\x00\x00\ x00\x02\x00\x00\ x00\x00\x00\x00 \x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\x00\xaaU\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    #    b'\x02\x00\x00\x00\xef\xcd\xab\x12\x00\x00\x00 \x00 \x00\x00\x00\x00\ x00\x00\x02\x00\ x00\x00\x00\x00 \x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\x00\x00\xaaU\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
       # b'\x02\x00\x00\x00\xef\xcd\xab\x12\x00\x00\x00@\x00 \x00\x00\x00\x00\ x00\x02\x00\x00\ x00\x00\x00\x00 \x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\x00\x00\ x00\x00\xaaU\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
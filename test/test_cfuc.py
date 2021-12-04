#!/usr/bin/env python
# coding: utf-8

"""
This module is for CFUC testing the serial interface, UCANDevices
"""


import unittest
import can
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


    def test_rx_tx_min_max_data(self):
        """
        Tests the transfer of init frame
        """
        self.bus = can.Bus(bustype="cfuc", channel="loop://", CANBaudRate=250000, IsFD=True, FDDataBaudRate=500000)
        self.serial = self.bus.ser
        msg = self.serial.read(self.serial.in_waiting)
        # msg = self.bus.recv(0)
        self.assertIsNotNone(msg)
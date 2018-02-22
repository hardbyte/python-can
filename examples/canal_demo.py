#!/usr/bin/env python
# coding: utf-8

"""
This demo shows a usage of an Lawicel CANUSB device.

Note: The CANAL interface is only designed to work with Windows.
"""

from __future__ import print_function

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

from can import Message, CanError
from can.interface import Bus

# import logging
# logging.basicConfig(level=logging.DEBUG)

serialMatcher = "PID_6001"
dll = "canusbdrv64.dll"
bus = Bus(bustype="canal", dll=dll, serialMatcher=serialMatcher, bitrate=100000, flags=0x4)

# alternatively, specify the device serial like this:
# bus = can.interface.Bus(bustype="canal", dll=dll, serial="LW19ZSBR", bitrate=100000, flags=0x4)

def send_one():
    msg = Message(arbitration_id=0x00c0ffee,
                      data=[0, 25, 0, 1, 3, 1, 4, 1],
                      extended_id=True)
    try:
        bus.send(msg)
        print("Message sent:", msg)
    except CanError:
        print("ERROR: Message send failure")

def receive_one():
    print("Wait for CAN message...")
    try:
        # blocking receive
        msg = bus.recv(timeout=0)
        if msg:
            print("Message received:", msg)
        else:
            print("ERROR: Unexpected bus.recv reply")

    except CanError:
        print("ERROR: Message not received")

if __name__ == '__main__':
    print("=====  CANAL interface demo =====")
    print("Device:", bus.channel_info)
    send_one()
    receive_one()

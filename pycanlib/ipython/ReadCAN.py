"""
File: ReadCAN.py

This file contains a subclass of ipipe.Table that can be used to read 
CAN traffic from a Kvaser CAN device.
"""

import ipipe
import sys, time

from pycanlib import CAN, canlib

class ReadCAN(ipipe.Table):
    """
    Class: ReadCAN
    Subclass of ipipe.Table used to read CAN traffic from a Kvaser CAN device.
    
    Parent class: ipipe.Table
    """
    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp):
        """
        Constructor: ReadCAN

        Parameters:
            channel, bitRate, tseg1, tseg2, sjw, noSamp: See
              CAN._Handle.__init__() for details
        """
        ipipe.Table.__init__(None)
        self.bus = CAN.Bus(channel=channel, speed=speed, tseg1=tseg1, 
          tseg2=tseg2, sjw=sjw, no_samp=no_samp,
          flags=canlib.canOPEN_ACCEPT_VIRTUAL)

    def __iter__(self):
        """Method: __iter__
        Reads received messages.
        
        Inputs: None
        """
        while True:
            try:
                message = self.bus.read()
                if message != None:
                    yield message
                else:
                    time.sleep(0.001)
            except KeyboardInterrupt:
                break

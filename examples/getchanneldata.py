"""
getchanneldata.py: an example script illustrating access to
channel data available for a CAN bus channels connected to a
computer.

Copyright (C) 2010 Dynamic Controls
"""
import ctypes
import sys
import time

from pycanlib import CAN, canlib

if __name__ == "__main__":
    print CAN.get_host_machine_info()
    _num_channels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
    for _channel in xrange(0, _num_channels.value):
        _bus = CAN.Bus(_channel, 1000000, 4, 3, 1, 3)
        print _bus.channel_info
        _bus.shutdown()


time.sleep(1)

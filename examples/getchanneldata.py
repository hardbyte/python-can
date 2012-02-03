"""
An example script illustrating access to
channel data available for a CAN bus channels connected to a
computer.
"""
import ctypes
import sys
import time

from pycanlib import CAN

if __name__ == "__main__":
    print(CAN.get_host_machine_info())

    num_channels = ctypes.c_int(0)
    #canlib.canGetNumberOfChannels(ctypes.byref(num_channels))
    for channel in range(0, 3):
        bus = CAN.Bus(channel, 1000000, 4, 3, 1, 3)
        print(bus.channel_info)
        bus.shutdown()


time.sleep(1)

import ctypes
import sys
import time

from pycanlib import CAN, canlib

if __name__ == "__main__":
    [sys.stdout.write("%s\n" % _line) for _line in CAN.get_host_machine_info().__str__().split("\n")]
    _num_channels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
    for _channel in xrange(0, _num_channels.value):
        _bus = CAN.Bus(_channel, 1000000, 4, 3, 1, 3)
        [sys.stdout.write("%s\n" % _line) for _line in _bus.channel_info.__str__().split("\n")]
        _bus.shutdown()
    time.sleep(1)


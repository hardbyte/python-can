import ctypes
import logging
import sys

from pycanlib import CAN, canlib

logging.basicConfig(level=logging.WARNING)

print "-"*64
print "Host machine info"
print "-"*64
print "OS:", CAN.GetHostMachineInfo()["osType"]
print "Python:", CAN.GetHostMachineInfo()["pythonVersion"]
print "CANLIB:", CAN.GetCANLIBInfo()
print "pycanlib:", CAN.__version__
print "-"*64
names = ["foo", "bar", "bork", "baz"]
buses = {}
canlib.canInitializeLibrary()
_numChannels = ctypes.c_int(0)
canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
for channel in xrange(0, _numChannels.value):
    print "CANLIB channel %d:" % channel
    buses[channel] = CAN.Bus(channel, canlib.canOPEN_ACCEPT_VIRTUAL, 105263, 10, 8, 4, 1, name=names[channel])
    print buses[channel].GetChannelInfo()
    print "-"*64

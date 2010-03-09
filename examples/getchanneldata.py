import ctypes
import logging
import sys

from pycanlib import CAN, canlib

def SetupLogging():
    loggerObj = logging.getLogger("getchanneldata")
    loggerObj.setLevel(logging.INFO)
    _logStreamHandler = logging.StreamHandler()
    _logFormatter = logging.Formatter("%(message)s")
    _logStreamHandler.setFormatter(_logFormatter)
    loggerObj.addHandler(_logStreamHandler)
    return loggerObj

def main():
    _loggerObj = SetupLogging()
    [_loggerObj.info(_line) for _line in CAN.get_host_machine_info().__str__().split("\n")]
    buses = {}
    canlib.canInitializeLibrary()
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    for channel in xrange(0, _numChannels.value):
        buses[channel] = CAN.Bus(channel, 1000000, 4, 3, 1, 3)
        for line in buses[channel].channel_info.__str__().split("\n"):
            _loggerObj.info(line)

if __name__ == "__main__":
    main()
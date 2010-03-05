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
    _loggerObj.info("-"*64)
    _loggerObj.info("Host machine info")
    _loggerObj.info("-"*64)
    _loggerObj.info("OS: %s" % CAN.get_host_machine_info().os_type)
    _loggerObj.info("Python: %s" % CAN.get_host_machine_info().python_version)
    _loggerObj.info("CANLIB: %s" % CAN.get_canlib_info())
    _loggerObj.info("pycanlib: %s" % CAN.__version__)
    _loggerObj.info("-"*64)
    buses = {}
    canlib.canInitializeLibrary()
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    for channel in xrange(0, _numChannels.value):
        buses[channel] = CAN.Bus(channel, 1000000, 4, 3, 1, 3)
        for line in buses[channel].channel_info.__str__().split("\n"):
            _loggerObj.info(line)
        _loggerObj.info("-"*64)

if __name__ == "__main__":
    main()
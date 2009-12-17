import ctypes
import logging
import nose
import random
import sys
import time
import types

from pycanlib import canlib, canstat, CAN


testLogger = logging.getLogger("pycanlib.test")


def setup():
    canlib.canInitializeLibrary()
    _numChannels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_numChannels))
    numChannels = _numChannels.value
    #We need to verify that all of pycanlib's functions operate correctly
    #on both virtual and physical channels, so we need to find at least one
    #of each to test with
    physicalChannels = []
    virtualChannels = []
    for _channel in xrange(numChannels):
        _cardType = ctypes.c_int(0)
        canlib.canGetChannelData(_channel,
          canlib.canCHANNELDATA_CARD_TYPE, ctypes.byref(_cardType), 4)
        if _cardType.value == canlib.canHWTYPE_VIRTUAL:
            virtualChannels.append(_channel)
        elif _cardType.value != canlib.canHWTYPE_NONE:
            physicalChannels.append(_channel)
    testLogger.debug("numChannels = %d" % numChannels)
    testLogger.debug("virtualChannels = %s" % virtualChannels)
    testLogger.debug("physicalChannels = %s" % physicalChannels)
    if len(virtualChannels) == 0:
        raise Exception("No virtual channels available for testing")
    elif len(physicalChannels) == 0:
        raise Exception("No physical channels available for testing")

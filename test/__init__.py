import ctypes
import logging
import types

from pycanlib import canlib, canstat, CAN

_test_logger = logging.getLogger("pycanlib.test")

def setup():
    canlib.canInitializeLibrary()
    _num_channels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
    _num_channels = _num_channels.value
    #We need to verify that all of pycanlib's functions operate correctly
    #on both virtual and physical channels, so we need to find at least one
    #of each to test with
    _physical_channels = []
    _virtual_channels = []
    for _channel in xrange(_num_channels):
        _card_type = ctypes.c_int(0)
        canlib.canGetChannelData(_channel,
          canlib.canCHANNELDATA_CARD_TYPE, ctypes.byref(_card_type), 4)
        if _card_type.value == canlib.canHWTYPE_VIRTUAL:
            _virtual_channels.append(_channel)
        elif _card_type.value != canlib.canHWTYPE_NONE:
            _physical_channels.append(_channel)
    if len(_virtual_channels) == 0:
        raise Exception("No virtual channels available for testing")
    elif len(_physical_channels) == 0:
        raise Exception("No physical channels available for testing")

def testShallNotAcceptInvalidTimestamps():
    for _timestamp in ["foo", -5, -1.0, 0.0, 1, 1.0, 2.5, 10000, 10000.2, True, False]:
        yield __isTimestampValid, _timestamp

def __isTimestampValid(timestamp):
    _msg_object = None
    try:
        _msg_object = CAN.Message(timestamp=timestamp)
    except Exception as e:
        _test_logger.debug("Exception thrown by CAN.Message", exc_info=True)
    if isinstance(timestamp, types.FloatType) and (timestamp >= 0):
        assert (_msg_object is not None)
        assert _msg_object.timestamp == timestamp
    else:
        assert (_msg_object is None)

def testShallNotAcceptInvalidRemoteFrameFlag():
    for _flag in ["foo", CAN.REMOTE_FRAME, CAN.DATA_FRAME, 1, 10, []]:
        yield __isRemoteFrameFlagValid, _flag

def __isRemoteFrameFlagValid(flag):
    _msg_object = None
    try:
        _msg_object = CAN.Message(is_remote_frame=flag)
    except Exception as e:
        _test_logger.debug("Exception thrown by CAN.Message", exc_info=True)
    if (flag in (CAN.REMOTE_FRAME, CAN.DATA_FRAME)) and isinstance(flag, types.BooleanType):
        assert (_msg_object is not None)
        assert _msg_object.is_remote_frame == flag
    else:
        assert (_msg_object is None)

def testDefaultRemoteFrameFlag():
    _msg_object = CAN.Message()
    assert (_msg_object.is_remote_frame == False)

def testShallNotAcceptInvalidIDTypeFlag():
    for _flag in ["foo", CAN.ID_TYPE_EXT, CAN.ID_TYPE_STD, 1, 10, []]:
        yield __isIDTypeFlagValid, _flag

def __isIDTypeFlagValid(flag):
    _msg_object = None
    try:
        _msg_object = CAN.Message(id_type=flag)
    except Exception as e:
        _test_logger.debug("Exception thrown by CAN.Message", exc_info=True)
    if (flag in (CAN.ID_TYPE_EXT, CAN.ID_TYPE_STD)) and isinstance(flag, types.BooleanType):
        assert (_msg_object is not None)
        assert _msg_object.id_type == flag
    else:
        assert (_msg_object is None)

def testShallNotAcceptInvalidWakeupFlag():
    for _flag in ["foo", CAN.WAKEUP_MSG, (not CAN.WAKEUP_MSG), 1, 10, []]:
        yield __isWakeupFlagValid, _flag

def __isWakeupFlagValid(flag):
    _msg_object = None
    try:
        _msg_object = CAN.Message(is_wakeup=flag)
    except Exception as e:
        _test_logger.debug("Exception thrown by CAN.Message", exc_info=True)
    if (flag in (CAN.WAKEUP_MSG, (not CAN.WAKEUP_MSG))) and isinstance(flag, types.BooleanType):
        assert (_msg_object is not None)
        assert _msg_object.is_wakeup == flag
    else:
        assert (_msg_object is None)

def testShallNotAcceptInvalidErrorFrameFlag():
    for _flag in ["foo", CAN.ERROR_FRAME, (not CAN.ERROR_FRAME), 1, 10, []]:
        yield __isErrorFrameFlagValid, _flag

def __isErrorFrameFlagValid(flag):
    _msg_object = None
    try:
        _msg_object = CAN.Message(is_error_frame=flag)
    except Exception as e:
        _test_logger.debug("Exception thrown by CAN.Message", exc_info=True)
    if (flag in (CAN.ERROR_FRAME, (not CAN.ERROR_FRAME))) and isinstance(flag, types.BooleanType):
        print _msg_object
        assert (_msg_object is not None)
        assert _msg_object.is_error_frame == flag
    else:
        print _msg_object
        assert (_msg_object is None)


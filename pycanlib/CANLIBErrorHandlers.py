import ctypes
import types

import canlib
import canstat


class CANLIBError(Exception):

    def __init__(self, function, errorCode, arguments):
        Exception.__init__(self)
        self.errorCode = errorCode
        self.functionName = function.__name__
        self.arguments = arguments

    def __str__(self):
        return ("CANLIBError: function %s failed - %s - arguments were %s" %
          (self.functionName, GetErrorMessage(self.errorCode),
          self.arguments))


def GetErrorMessage(result):
    errmsg = ctypes.create_string_buffer(128)
    canlib.canGetErrorText(result, errmsg, len(errmsg))
    return ("%s (code %d)" % (errmsg.value, result))


def _HandleValid(handle):
    return (handle >= 0)


def CheckBusHandleValidity(handle, function, arguments):
    if not _HandleValid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle


def _ConvertCANStatusToInt(result):
    if isinstance(result, (types.IntType, types.LongType)):
        _result = result
    else:
        _result = result.value
    return _result


def CheckStatus(result, function, arguments):
    _result = _ConvertCANStatusToInt(result)
    if not canstat.CANSTATUS_SUCCESS(_result):
        raise CANLIBError(function, _result, arguments)
    else:
        return result


def CheckStatusRead(result, function, arguments):
    _result = _ConvertCANStatusToInt(result)
    if not canstat.CANSTATUS_SUCCESS(_result) and \
      (_result != canstat.canERR_NOMSG):
        raise CANLIBError(function, _result, arguments)
    else:
        return result

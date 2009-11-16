import ctypes

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
          (self.functionName, GetErrorMessage(self.errorCode.value),
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


def CheckStatus(result, function, arguments):
    if not canstat.CANSTATUS_SUCCESS(result.value):
        raise CANLIBError(function, result, arguments)
    else:
        return result


def CheckStatusRead(result, function, arguments):
    if not canstat.CANSTATUS_SUCCESS(result.value) and \
      (result.value != canERR_NOMSG):
        raise CANLIBError(function, result, arguments)
    else:
        return result

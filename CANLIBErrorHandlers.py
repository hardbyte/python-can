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
    errmsg = create_string_buffer(128)
    canlib.canGetErrorText(result, errmsg, len(errmsg))
    if type(result) == types.IntType:
        retVal = ("%s (code %d)" % (errmsg.value, result))
    else:
        retVal = ("%s (code %d)" % (errmsg.value, result.value))
    return retVal


def CheckBusHandleValidity(handle, function, arguments):
    if not is_handle_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle


def CheckStatus(result, function, arguments):
    if not CANSTATUS_SUCCESS(result):
        raise CANLIBError(function, result, arguments)
    else:
        return result


def CheckStatusRead(result, function, arguments):
    if not canstat.CANSTATUS_SUCCESS(result) and \
      (result.value != canERR_NOMSG):
        raise CANLIBError(function, result, arguments)
    else:
        return result

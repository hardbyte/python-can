
from canlib import *
from canstat import *

class CANLIBError(Exception):
    def __init__(self, function, errorCode, arguments):
        Exception.__init__(self)
        self.errorCode = errorCode
        self.functionName = function.__name__
        self.arguments = arguments

    def __str__(self):
        return ("CANLIBError: function %s failed - %s (arguments were %s)" % 
          (self.functionName, GetErrorMessage(self.errorCode), self.arguments))

def GetErrorMessage(result):
    errmsg = create_string_buffer(128)
    canGetErrorText(result, errmsg, len(errmsg))
    if type(result) == types.IntType:
        retVal = ("%s (code %d)" % (errmsg.value, result))
    else:
        retVal = ("%s (code %d)" % (errmsg.value, result.value))
    return retVal

# function to check result of a function returning a CAN handle
#borrowed from Phillip Dixon's Kvaser Python library
def CheckBusHandleValidity(handle, function, arguments):
    # abort if handle invalid 
    if not is_handle_valid(handle):
        raise CANLIBError(function, handle, arguments)
    # else return the handle
    else:
        return handle

# general function to check result of a function returning a CAN status
#borrowed from Phillip Dixon's Kvaser Python library
def CheckStatus(result, function, arguments):
    # abort if failure 
    if not CANSTATUS_SUCCESS(result):
        raise CANLIBError(function, result, arguments)
    # else return the status
    else:
        return result

# function to check result of a CAN read function returning a CAN status
#borrowed from Phillip Dixon's Kvaser Python library
def CheckStatusRead(result, function, arguments):
    # abort if failure - for Read functions, no message is not an error 
    if not CANSTATUS_SUCCESS(result) and (result.value != canERR_NOMSG):
        raise CANLIBError(function, result, arguments)
    # else return the status
    else:
        return result

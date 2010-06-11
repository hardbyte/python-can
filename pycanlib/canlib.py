import ctypes
import sys
import types

from pycanlib import canstat

if sys.platform == "win32":
    __canlib = ctypes.windll.LoadLibrary("canlib32")
else:
    __canlib = ctypes.cdll.LoadLibrary("libcanlib.so")

def __get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    retval = eval("__canlib.%s" % func_name)
    retval.argtypes = argtypes
    retval.restype = restype
    retval.errcheck = errcheck
    return retval

class CANLIBError(Exception):

    def __init__(self, function, error_code, arguments):
        Exception.__init__(self)
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return ("function %s failed - %s - arguments were %s" % (self.function.__name__, self.__get_error_message(), self.arguments))

    def __get_error_message(self):
        errmsg = ctypes.create_string_buffer(128)
        canGetErrorText(self.error_code, errmsg, len(errmsg))
        return ("%s (code %d)" % (errmsg.value, self.error_code))

def __convert_can_status_to_int(result):
    if isinstance(result, (types.IntType, types.LongType)):
        _result = result
    else:
        _result = result.value
    return _result

def __check_status(result, function, arguments):
    _result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result):
        raise CANLIBError(function, _result, arguments)
    else:
        return result

def __check_status_read(result, function, arguments):
    _result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result) and (_result != canstat.canERR_NOMSG):
        raise CANLIBError(function, _result, arguments)
    else:
        return result

class c_canHandle(ctypes.c_int):
    pass

canINVALID_HANDLE = -1

def __handle_is_valid(handle):
    return (handle > canINVALID_HANDLE)

def __check_bus_handle_validity(handle, function, arguments):
    if not __handle_is_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle

canInitializeLibrary = __get_canlib_function("canInitializeLibrary", argtypes=[], restype=canstat.c_canStatus, errcheck=__check_status)

canGetErrorText = __get_canlib_function("canGetErrorText", argtypes=[canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canGetNumberOfChannels = __get_canlib_function("canGetNumberOfChannels", argtypes=[ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=__check_status)

if sys.platform == "win32":
    __canReadTimer_func_name = "kvReadTimer"
else:
    __canReadTimer_func_name = "canReadTimer"
canReadTimer = __get_canlib_function(__canReadTimer_func_name, argtypes=[c_canHandle, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=__check_status)

canBusOff = __get_canlib_function("canBusOff", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=__check_status)

canBusOn = __get_canlib_function("canBusOn", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=__check_status)

canClose = __get_canlib_function("canClose", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=__check_status)

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200
FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED | canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE | canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS | canOPEN_ACCEPT_LARGE_DLC)
canOpenChannel = __get_canlib_function("canOpenChannel", argtypes=[ctypes.c_int, ctypes.c_int], restype=ctypes.c_int, errcheck=__check_bus_handle_validity)

canSetBusParams = __get_canlib_function("canSetBusParams", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0
canSetBusOutputControl = __get_canlib_function("canSetBusOutputControl", argtypes=[ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canReadWait = __get_canlib_function("canReadWait", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long], restype=canstat.c_canStatus, errcheck=__check_status_read)

canWriteWait = __get_canlib_function("canWriteWait", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=__check_status)

canIOCTL_GET_RX_BUFFER_LEVEL = 8
canIOCTL_GET_TX_BUFFER_LEVEL = 9
canIOCTL_FLUSH_RX_BUFFER = 10
canIOCTL_FLUSH_TX_BUFFER = 11
canIOCTL_GET_TIMER_SCALE = 12
canIOCTL_SET_TXRQ = 13
canIOCTL_GET_EVENTHANDLE = 14
canIOCTL_SET_BYPASS_MODE = 15
canIOCTL_SET_WAKEUP = 16
canIOCTL_GET_DRIVERHANDLE = 17
canIOCTL_MAP_RXQUEUE = 18
canIOCTL_GET_WAKEUP = 19
canIOCTL_SET_REPORT_ACCESS_ERRORS = 20
canIOCTL_GET_REPORT_ACCESS_ERRORS = 21
canIOCTL_CONNECT_TO_VIRTUAL_BUS = 22
canIOCTL_DISCONNECT_FROM_VIRTUAL_BUS = 23
canIOCTL_SET_USER_IOPORT = 24
canIOCTL_GET_USER_IOPORT = 25
canIOCTL_SET_BUFFER_WRAPAROUND_MODE = 26
canIOCTL_SET_RX_QUEUE_SIZE = 27
canIOCTL_SET_USB_THROTTLE = 28
canIOCTL_GET_USB_THROTTLE = 29
canIOCTL_SET_BUSON_TIME_AUTO_RESET = 30
canIOCTL_PREFER_EXT = 1
canIOCTL_PREFER_STD = 2
canIOCTL_CLEAR_ERROR_COUNTERS = 5
canIOCTL_SET_TIMER_SCALE = 6
canIOCTL_SET_TXACK = 7
canIoCtl = __get_canlib_function("canIoCtl", argtypes=[ctypes.c_int, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

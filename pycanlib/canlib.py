import ctypes
import sys
import types

from pycanlib import canstat

if sys.platform == "win32":
    __canlib = ctypes.windll.LoadLibrary("canlib32")
else:
    __canlib = ctypes.cdll.LoadLibrary("libcanlib.so")

def __get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    try:
        retval = eval("__canlib.%s" % func_name)
    except AttributeError:
        return None
    else:
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

canBusOff = __get_canlib_function("canBusOff", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canBusOn = __get_canlib_function("canBusOn", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canClose = __get_canlib_function("canClose", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200
FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED | canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE | canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS | canOPEN_ACCEPT_LARGE_DLC)
canOpenChannel = __get_canlib_function("canOpenChannel", argtypes=[ctypes.c_int, ctypes.c_int], restype=c_canHandle, errcheck=__check_bus_handle_validity)

canSetBusParams = __get_canlib_function("canSetBusParams", argtypes=[c_canHandle, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0
canSetBusOutputControl = __get_canlib_function("canSetBusOutputControl", argtypes=[c_canHandle, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canReadWait = __get_canlib_function("canReadWait", argtypes=[c_canHandle, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long], restype=canstat.c_canStatus, errcheck=__check_status_read)

canWriteWait = __get_canlib_function("canWriteWait", argtypes=[c_canHandle, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=__check_status)

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
canIoCtl = __get_canlib_function("canIoCtl", argtypes=[c_canHandle, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canGetVersion = __get_canlib_function("canGetVersion", restype=ctypes.c_short, errcheck=__check_status)

canTRANSCEIVER_TYPE_UNKNOWN = 0
canTRANSCEIVER_TYPE_251 = 1
canTRANSCEIVER_TYPE_252 = 2
canTRANSCEIVER_TYPE_DNOPTO = 3
canTRANSCEIVER_TYPE_W210 = 4
canTRANSCEIVER_TYPE_SWC_PROTO = 5
canTRANSCEIVER_TYPE_SWC = 6
canTRANSCEIVER_TYPE_EVA = 7
canTRANSCEIVER_TYPE_FIBER = 8
canTRANSCEIVER_TYPE_K251 = 9
canTRANSCEIVER_TYPE_K = 10
canTRANSCEIVER_TYPE_1054_OPTO = 11
canTRANSCEIVER_TYPE_SWC_OPTO = 12
canTRANSCEIVER_TYPE_TT = 13
canTRANSCEIVER_TYPE_1050 = 14
canTRANSCEIVER_TYPE_1050_OPTO = 15
canTRANSCEIVER_TYPE_1041 = 16
canTRANSCEIVER_TYPE_1041_OPTO = 17
canTRANSCEIVER_TYPE_RS485 = 18
canTRANSCEIVER_TYPE_LIN = 19
canTRANSCEIVER_TYPE_KONE = 20
canTRANSCEIVER_TYPE_LINX_LIN = 64
canTRANSCEIVER_TYPE_LINX_J1708 = 66
canTRANSCEIVER_TYPE_LINX_K = 68
canTRANSCEIVER_TYPE_LINX_SWC = 70
canTRANSCEIVER_TYPE_LINX_LS = 72

canTransceiverTypeStrings = {canTRANSCEIVER_TYPE_UNKNOWN: "unknown",
                             canTRANSCEIVER_TYPE_251: "82C251",
                             canTRANSCEIVER_TYPE_252: "82C252/TJA1053/TJA1054",
                             canTRANSCEIVER_TYPE_DNOPTO: "Optoisolated 82C251",
                             canTRANSCEIVER_TYPE_W210: "W210",
                             canTRANSCEIVER_TYPE_SWC_PROTO: "AU5790 prototype",
                             canTRANSCEIVER_TYPE_SWC: "AU5790",
                             canTRANSCEIVER_TYPE_EVA: "EVA",
                             canTRANSCEIVER_TYPE_FIBER: "82C251 with fibre extension",
                             canTRANSCEIVER_TYPE_K251: "K251",
                             canTRANSCEIVER_TYPE_K: "K",
                             canTRANSCEIVER_TYPE_1054_OPTO: "TJA1054 optical isolation",
                             canTRANSCEIVER_TYPE_SWC_OPTO: "AU5790 optical isolation",
                             canTRANSCEIVER_TYPE_TT: "B10011S Truck-And-Trailer",
                             canTRANSCEIVER_TYPE_1050: "TJA1050",
                             canTRANSCEIVER_TYPE_1050_OPTO: "TJA1050 optical isolation",
                             canTRANSCEIVER_TYPE_1041: "TJA1041",
                             canTRANSCEIVER_TYPE_1041_OPTO: "TJA1041 optical isolation",
                             canTRANSCEIVER_TYPE_RS485: "RS485",
                             canTRANSCEIVER_TYPE_LIN: "LIN",
                             canTRANSCEIVER_TYPE_KONE: "KONE",
                             canTRANSCEIVER_TYPE_LINX_LIN: "LINX_LIN",
                             canTRANSCEIVER_TYPE_LINX_J1708: "LINX_J1708",
                             canTRANSCEIVER_TYPE_LINX_K: "LINX_K",
                             canTRANSCEIVER_TYPE_LINX_SWC: "LINX_SWC",
                             canTRANSCEIVER_TYPE_LINX_LS: "LINX_LS"}

def lookup_transceiver_type(type):
    try:
        return canTransceiverTypeStrings[type]
    except KeyError:
        return "unknown"

canCHANNELDATA_CHANNEL_CAP = 1
canCHANNELDATA_TRANS_CAP = 2
canCHANNELDATA_CHANNEL_FLAGS = 3
canCHANNELDATA_CARD_TYPE = 4
canCHANNELDATA_CARD_NUMBER = 5
canCHANNELDATA_CHAN_NO_ON_CARD = 6
canCHANNELDATA_CARD_SERIAL_NO = 7
canCHANNELDATA_TRANS_SERIAL_NO = 8
canCHANNELDATA_CARD_FIRMWARE_REV = 9
canCHANNELDATA_CARD_HARDWARE_REV = 10
canCHANNELDATA_CARD_UPC_NO = 11
canCHANNELDATA_TRANS_UPC_NO = 12
canCHANNELDATA_CHANNEL_NAME = 13
canCHANNELDATA_DLL_FILE_VERSION = 14
canCHANNELDATA_DLL_PRODUCT_VERSION = 15
canCHANNELDATA_DLL_FILETYPE = 16
canCHANNELDATA_TRANS_TYPE = 17
canCHANNELDATA_DEVICE_PHYSICAL_POSITION = 18
canCHANNELDATA_UI_NUMBER = 19
canCHANNELDATA_TIMESYNC_ENABLED = 20
canCHANNELDATA_DRIVER_FILE_VERSION = 21
canCHANNELDATA_DRIVER_PRODUCT_VERSION = 22
canCHANNELDATA_MFGNAME_UNICODE = 23
canCHANNELDATA_MFGNAME_ASCII = 24
canCHANNELDATA_DEVDESCR_UNICODE = 25
canCHANNELDATA_DEVDESCR_ASCII = 26
canCHANNELDATA_DRIVER_NAME = 27
canGetChannelData = __get_canlib_function("canGetChannelData", argtypes=[c_canHandle, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=canstat.c_canStatus, errcheck=__check_status)

import ctypes
import sys
import types

from pycanlib import canstat

canINVALID_HANDLE = -1

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200
FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED | canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE | canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS | canOPEN_ACCEPT_LARGE_DLC)

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

def _get_canlib():
    if sys.platform == "win32":
        return ctypes.windll.LoadLibrary("canlib32")
    else:
        return ctypes.cdll.LoadLibrary("libcanlib.so")

def _get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    retval = None
    try:
        retval = eval("_get_canlib().%s" % func_name)
    except AttributeError:
        sys.stderr.write("Function %s is unavailable - this is CANLIB %s\n" % (func_name, _get_canlib_version_string()))
        retval = None
    if retval != None:
        if argtypes != None:
            retval.argtypes = argtypes
        if restype != None:
            retval.restype = restype
        if errcheck != None:
            retval.errcheck = errcheck
    return retval

def _get_canlib_version_string():
    try:
        canlib_version = _get_canlib().canGetVersionEx(2)
        canlib_major_version = ((canlib_version & 0x00FF0000) >> 16)
        canlib_minor_version = ((canlib_version & 0x0000FF00) >> 8)
        canlib_version_letter = ("%c" % (canlib_version & 0x000000FF))
        retval = "%d.%d%s" % (canlib_major_version, canlib_minor_version, canlib_version_letter)
    except Exception as e:
        print "Can't determine CANLIB version - %s" % e.msg
        retval = "<unknown>"
    return retval

def _check_status(result, function, arguments):
    _result = _convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result):
        raise CANLIBError(function, _result, arguments)
    else:
        return result

def _check_status_read(result, function, arguments):
    _result = _convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result) and (_result != canstat.canERR_NOMSG):
        raise CANLIBError(function, _result, arguments)
    else:
        return result

def _convert_can_status_to_int(result):
    if isinstance(result, (types.IntType, types.LongType)):
        _result = result
    else:
        _result = result.value
    return _result

class CANLIBError(Exception):

    def __init__(self, function, error_code, arguments):
        Exception.__init__(self)
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return ("function %s failed - %s - arguments were %s" % (self.function.__name__, _get_error_message(self.error_code), self.arguments))

def _handle_is_valid(handle):
    return (handle >= 0)

def _check_bus_handle_validity(handle, function, arguments):
    if not _handle_is_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle

canInitializeLibrary = _get_canlib_function("canInitializeLibrary", argtypes=[], restype=canstat.c_canStatus, errcheck=_check_status)
canGetNumberOfChannels = _get_canlib_function("canGetNumberOfChannels", argtypes=[ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canOpenChannel = _get_canlib_function("canOpenChannel", argtypes=[ctypes.c_int, ctypes.c_int], restype=ctypes.c_int, errcheck=_check_bus_handle_validity)
canIoCtl = _get_canlib_function("canIoCtl", argtypes=[ctypes.c_int, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canClose = _get_canlib_function("canClose", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canBusOn = _get_canlib_function("canBusOn", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canBusOff = _get_canlib_function("canBusOff", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canSetBusParams = _get_canlib_function("canSetBusParams", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canGetBusParams = _get_canlib_function("canGetBusParams", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canSetBusOutputControl = _get_canlib_function("canSetBusOutputControl", argtypes=[ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canGetBusOutputControl = _get_canlib_function("canGetBusOutputControl", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canReadWait = _get_canlib_function("canReadWait", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long], restype=canstat.c_canStatus, errcheck=_check_status_read)

"""
callback_dict = {"win32": ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int), "posix": ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int)}

def _get_error_message(result):
    errmsg = ctypes.create_string_buffer(128)
    canGetErrorText(result, errmsg, len(errmsg))
    return ("%s (code %d)" % (errmsg.value, result))

class c_canHandle(ctypes.c_int):
    pass

class c_canBusStatistics(ctypes.Structure):
    _fields_ = [("std_data", ctypes.c_ulong), ("std_remote", ctypes.c_ulong), ("ext_data", ctypes.c_ulong), ("ext_remote", ctypes.c_ulong), ("error_frames", ctypes.c_ulong), ("bus_load", ctypes.c_ulong), ("overruns", ctypes.c_ulong)]

class c_kvStatus(canstat.c_canStatus):
    pass

kvBUSTYPE_NONE = 0
kvBUSTYPE_PCI = 1
kvBUSTYPE_PCMCIA = 2
kvBUSTYPE_USB = 3
kvBUSTYPE_WLAN = 4
kvBUSTYPE_PCI_EXPRESS = 5
kvBUSTYPE_ISA = 6
kvBUSTYPE_VIRTUAL = 7
kvBUSTYPE_PC104_PLUS = 8

CALLBACKFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
NULL_CALLBACK = ctypes.cast(None, CALLBACKFUNC)

canFILTER_ACCEPT = 1
canFILTER_REJECT = 2
canFILTER_SET_CODE_STD = 3
canFILTER_SET_MASK_STD = 4
canFILTER_SET_CODE_EXT = 5
canFILTER_SET_MASK_EXT = 6

canFILTER_NULL_MASK = 0L

canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0

canBITRATE_1M = (-1)
canBITRATE_500K = (-2)
canBITRATE_250K = (-3)
canBITRATE_125K = (-4)
canBITRATE_100K = (-5)
canBITRATE_62K = (-6)
canBITRATE_50K = (-7)
canBITRATE_83K = (-8)
canBITRATE_10K = (-9)

BAUD_1M = (-1)
BAUD_500K = (-2)
BAUD_250K = (-3)
BAUD_125K = (-4)
BAUD_100K = (-5)
BAUD_62K = (-6)
BAUD_50K = (-7)
BAUD_83K = (-8)


CANID_METAMSG = (-1L)
CANID_WILDCARD = (-2L)

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

canCHANNEL_IS_EXCLUSIVE = 0x0001
canCHANNEL_IS_OPEN = 0x0002

canHWTYPE_NONE = 0
canHWTYPE_VIRTUAL = 1
canHWTYPE_LAPCAN = 2
canHWTYPE_CANPARI = 3
canHWTYPE_PCCAN = 8
canHWTYPE_PCICAN = 9
canHWTYPE_USBCAN = 11
canHWTYPE_PCICAN_II = 40
canHWTYPE_USBCAN_II = 42
canHWTYPE_SIMULATED = 44
canHWTYPE_ACQUISITOR = 46
canHWTYPE_LEAF = 48
canHWTYPE_PC104_PLUS = 50
canHWTYPE_PCICANX_II = 52
canHWTYPE_MEMORATOR_II = 54
canHWTYPE_MEMORATOR_PRO = 54
canHWTYPE_USBCAN_PRO = 56
canHWTYPE_IRIS = 58
canHWTYPE_BLACKBIRD = 58
canHWTYPE_MEMORATOR_LIGHT = 60

canCHANNEL_CAP_EXTENDED_CAN = 0x00000001L
canCHANNEL_CAP_BUS_STATISTICS = 0x00000002L
canCHANNEL_CAP_ERROR_COUNTERS = 0x00000004L
canCHANNEL_CAP_CAN_DIAGNOSTICS = 0x00000008L
canCHANNEL_CAP_GENERATE_ERROR = 0x00000010L
canCHANNEL_CAP_GENERATE_OVERLOAD = 0x00000020L
canCHANNEL_CAP_TXREQUEST = 0x00000040L
canCHANNEL_CAP_TXACKNOWLEDGE = 0x00000080L
canCHANNEL_CAP_VIRTUAL = 0x00010000L
canCHANNEL_CAP_SIMULATED = 0x00020000L
canCHANNEL_CAP_REMOTE = 0x00040000L

canDRIVER_CAP_HIGHSPEED = 0x00000001L

canVERSION_CANLIB32_VERSION = 0
canVERSION_CANLIB32_PRODVER = 1
canVERSION_CANLIB32_PRODVER32 = 2
canVERSION_CANLIB32_BETA = 3

canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

ACCEPTANCE_FILTER_TYPE_STD = 0
ACCEPTANCE_FILTER_TYPE_EXT = 1

kvLED_ACTION_ALL_LEDS_ON = 0
kvLED_ACTION_ALL_LEDS_OFF = 1
kvLED_ACTION_LED_0_ON = 2
kvLED_ACTION_LED_0_OFF = 3
kvLED_ACTION_LED_1_ON = 4
kvLED_ACTION_LED_1_OFF = 5
kvLED_ACTION_LED_2_ON = 6
kvLED_ACTION_LED_2_OFF = 7
kvLED_ACTION_LED_3_ON = 8
kvLED_ACTION_LED_3_OFF = 9

canAccept = _get_canlib_function("canAccept", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canReadStatus = _get_canlib_function("canReadStatus", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canReadErrorCounters = _get_canlib_function("canReadErrorCounters", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canWrite = _get_canlib_function("canWrite", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canWriteSync = _get_canlib_function("canWriteSync", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canRead = _get_canlib_function("canRead", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status_read)
canReadSpecific = _get_canlib_function("canReadSpecific", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status_read)
canReadSync = _get_canlib_function("canReadSync", argtypes=[ctypes.c_int, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=_check_status_read)
canReadSyncSpecific = _get_canlib_function("canReadSyncSpecific", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=_check_status_read)
canReadSpecificSkip = _get_canlib_function("canReadSpecificSkip", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status_read)
canSetNotify = _get_canlib_function("canSetNotify", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canTranslateBaud = _get_canlib_function("canTranslateBaud", argtypes=[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canGetErrorText = _get_canlib_function("canGetErrorText", argtypes=[canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canGetVersion = _get_canlib_function("canGetVersion", argtypes=[], restype=ctypes.c_ushort)#canGetVersion doesn't return a canstat.c_canStatus value, so it has no error checking
canReadTimer = _get_canlib_function("canReadTimer", argtypes=[ctypes.c_int], restype=ctypes.c_ulong, errcheck=_check_status)
canGetChannelData = _get_canlib_function("canGetChannelData", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=canstat.c_canStatus, errcheck=_check_status)
canWaitForEvent = _get_canlib_function("canWaitForEvent", argtypes=[ctypes.c_int, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=_check_status)
canSetBusParamsC200 = _get_canlib_function("canSetBusParamsC200", argtypes=[ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte], restype=canstat.c_canStatus, errcheck=_check_status)
canSetDriverMode = _get_canlib_function("canSetDriverMode", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canGetDriverMode = _get_canlib_function("canGetDriverMode", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canGetVersionEx = _get_canlib_function("canGetVersionEx", argtypes=[ctypes.c_uint], restype=ctypes.c_uint)#canGetVersionEx doesn't return a canstat.c_canStatus value, so it has no error checking
canParamGetCount = _get_canlib_function("canParamGetCount", argtypes=[], restype=canstat.c_canStatus, errcheck=_check_status)
canParamCommitChanges = _get_canlib_function("canParamCommitChanges", argtypes=[], restype=canstat.c_canStatus, errcheck=_check_status)
canParamDeleteEntry = _get_canlib_function("canParamDeleteEntry", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canParamCreateNewEntry = _get_canlib_function("canParamCreateNewEntry", argtypes=[], restype=canstat.c_canStatus, errcheck=_check_status)
canParamSwapEntries = _get_canlib_function("canParamSwapEntries", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canParamGetName = _get_canlib_function("canParamGetName", argtypes=[ctypes.c_int, ctypes.c_char_p, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canParamGetChannelNumber = _get_canlib_function("canParamGetChannelNumber", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canParamGetBusParams = _get_canlib_function("canParamGetBusParams", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
canParamSetName = _get_canlib_function("canParamSetName", argtypes=[ctypes.c_int, ctypes.c_char_p], restype=canstat.c_canStatus, errcheck=_check_status)
canParamSetChannelNumber = _get_canlib_function("canParamSetChannelNumber", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canParamSetBusParams = _get_canlib_function("canParamSetBusParams", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canParamFindByName = _get_canlib_function("canParamFindByName", argtypes=[ctypes.c_char_p], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufFreeAll = _get_canlib_function("canObjBufFreeAll", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufAllocate = _get_canlib_function("canObjBufAllocate", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufFree = _get_canlib_function("canObjBufFree", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufWrite = _get_canlib_function("canObjBufWrite", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufSetFilter = _get_canlib_function("canObjBufSetFilter", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufSetFlags = _get_canlib_function("canObjBufSetFlags", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufSetPeriod = _get_canlib_function("canObjBufSetPeriod", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufSetMsgCount = _get_canlib_function("canObjBufSetMsgCount", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufEnable = _get_canlib_function("canObjBufEnable", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufDisable = _get_canlib_function("canObjBufDisable", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canObjBufSendBurst = _get_canlib_function("canObjBufSendBurst", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
canProbeVersion = _get_canlib_function("canProbeVersion", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=ctypes.c_bool)#canProbeVersion doesn't return a canstat.c_canStatus value, so it has no error checking
canResetBus = _get_canlib_function("canResetBus", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canWriteWait = _get_canlib_function("canWriteWait", argtypes=[ctypes.c_int, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=_check_status)
canUnloadLibrary = _get_canlib_function("canUnloadLibrary", argtypes=[], restype=canstat.c_canStatus, errcheck=_check_status)
canSetAcceptanceFilter = _get_canlib_function("canSetAcceptanceFilter", argtypes=[ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canFlushReceiveQueue = _get_canlib_function("canFlushReceiveQueue", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canFlushTransmitQueue = _get_canlib_function("canFlushTransmitQueue", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
kvGetApplicationMapping = _get_canlib_function("kvGetApplicationMapping", argtypes=[ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
kvBeep = _get_canlib_function("kvBeep", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=_check_status)
kvSelfTest = _get_canlib_function("kvSelfTest", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=_check_status)
kvFlashLeds = _get_canlib_function("kvFlashLeds", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canRequestChipStatus = _get_canlib_function("canRequestChipStatus", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canRequestBusStatistics = _get_canlib_function("canRequestBusStatistics", argtypes=[ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
canGetBusStatistics = _get_canlib_function("canGetBusStatistics", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=canstat.c_canStatus, errcheck=_check_status)
canSetBitrate = _get_canlib_function("canSetBitrate", argtypes=[ctypes.c_int, ctypes.c_int], restype=canstat.c_canStatus, errcheck=_check_status)
kvAnnounceIdentity = _get_canlib_function("kvAnnounceIdentity", argtypes=[ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=canstat.c_canStatus, errcheck=_check_status)
canGetHandleData = _get_canlib_function("canGetHandleData", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=canstat.c_canStatus, errcheck=_check_status)
kvTimeDomainCreate = _get_canlib_function("kvTimeDomainCreate", argtypes=[c_kvTimeDomain], restype=c_kvStatus, errcheck=_check_status)
kvTimeDomainDelete = _get_canlib_function("kvTimeDomainDelete", argtypes=[c_kvTimeDomain], restype=c_kvStatus, errcheck=_check_status)
kvTimeDomainResetTime = _get_canlib_function("kvTimeDomainResetTime", argtypes=[c_kvTimeDomain], restype=c_kvStatus, errcheck=_check_status)
kvTimeDomainGetData = _get_canlib_function("kvTimeDomainGetData", argtypes=[c_kvTimeDomain, ctypes.c_void_p, ctypes.c_size_t], restype=c_kvStatus, errcheck=_check_status)
kvTimeDomainAddHandle = _get_canlib_function("kvTimeDomainAddHandle", argtypes=[c_kvTimeDomain, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvTimeDomainRemoveHandle = _get_canlib_function("kvTimeDomainRemoveHandle", argtypes=[c_kvTimeDomain, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvSetNotifyCallback = _get_canlib_function("kvSetNotifyCallback", argtypes=[ctypes.c_int, c_kvCallback, ctypes.c_void_p, ctypes.c_uint], restype=c_kvStatus, errcheck=_check_status)
kvGetSupportedInterfaceInfo = _get_canlib_function("kvGetSupportedInterfaceInfo", argtypes=[ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
kvReadTimer = _get_canlib_function("kvReadTimer", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
kvReadTimer64 = _get_canlib_function("kvReadTimer64", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
kvReadDeviceCustomerData = _get_canlib_function("kvReadDeviceCustomerData", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t], restype=c_kvStatus, errcheck=_check_status)
kvScriptStart = _get_canlib_function("kvScriptStart", argtypes=[ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptStop = _get_canlib_function("kvScriptStop", argtypes=[ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptForceStop = _get_canlib_function("kvScriptForceStop", argtypes=[ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptSendEvent = _get_canlib_function("kvScriptSendEvent", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptEnvvarOpen = _get_canlib_function("kvScriptEnvvarOpen", argtypes=[ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p], restype = c_kvEnvHandle)#Since kvScriptEnvvarOpen doesn't return a status value, it has no error checking
kvScriptEnvvarClose = _get_canlib_function("kvScriptEnvvarClose", argtypes=[c_kvEnvHandle], restype=c_kvStatus, errcheck=_check_status)
kvScriptEnvvarSetInt = _get_canlib_function("kvScriptEnvvarSetInt", argtypes=[c_kvEnvHandle, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptEnvvarGetInt = _get_canlib_function("kvScriptEnvvarGetInt", argtypes=[c_kvEnvHandle, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
kvScriptEnvvarSetData = _get_canlib_function("kvScriptEnvvarSetData", argtypes=[c_kvEnvHandle, ctypes.c_void_p, ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptEnvvarGetData = _get_canlib_function("kvScriptEnvvarGetData", argtypes=[c_kvEnvHandle, ctypes.c_void_p, ctypes.c_int, ctypes.c_int], restype=c_kvStatus, errcheck=_check_status)
kvScriptGetMaxEnvvarSize = _get_canlib_function("kvScriptGetMaxEnvvarSize", argtypes=[ctypes.c_int, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
kvScriptLoadFileOnDevice = _get_canlib_function("kvScriptLoadFileOnDevice", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_char_p], restype=c_kvStatus, errcheck=_check_status)
kvScriptLoadFile = _get_canlib_function("kvScriptLoadFile", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_char_p], restype=c_kvStatus, errcheck=_check_status)
kvFileCopyToDevice = _get_canlib_function("kvFileCopyToDevice", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_char_p], restype=c_kvStatus, errcheck=_check_status)
kvFileCopyFromDevice = _get_canlib_function("kvFileCopyFromDevice", argtypes=[ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p], restype=c_kvStatus, errcheck=_check_status)
kvFileDelete = _get_canlib_function("kvFileDelete", argtypes=[ctypes.c_int, ctypes.c_char_p], restype=c_kvStatus, errcheck=_check_status)
kvFileGetSystemData = _get_canlib_function("kvFileGetSystemData", argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_void_p], restype=c_kvStatus, errcheck=_check_status)
"""
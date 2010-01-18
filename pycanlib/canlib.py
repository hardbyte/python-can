"""
File: canlib.py

This file is the canlib.h file from the CANLIB SDK translated into Python
using the ctypes package, and containing some improved error handling
(functions throw exceptions containing error information instead of returning
error codes).
"""


import ctypes
import sys
import types

from pycanlib import canstat

def _get_canlib():
    """
    Method: _get_canlib
    
    Returns: an object representing the CANLIB driver library, depending on the
    operating system pycanlib is running on.
    """
    #win32 = CPython on Windows
    #cli = IronPython on Windows
    #posix = CPython on *nix
    canlib_dict = {"win32": (ctypes.WinDLL, "canlib32.dll"),
                  "cli": (ctypes.CDLL, "canlib32.dll"),
                  "posix": (ctypes.CDLL, "libcanlib.so")}
    library_constructor = canlib_dict[sys.platform][0]
    library_name = canlib_dict[sys.platform][1]
    return library_constructor(library_name)


callback_dict = {"win32": ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int),
                 "cli": ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int),
                 "posix": ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int)}


class CANLIBError(Exception):
    """
    Class: CANLIBError
    
    Object used to represent errors indicated by CANLIB functions.
    
    Parent class: Exception
    """

    def __init__(self, function, error_code, arguments):
        Exception.__init__(self)
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return ("function %s failed - %s - arguments were %s" %
          (self.function.__name__, _get_error_message(self.error_code),
          self.arguments))


def _get_error_message(result):
    """
    Method: _get_error_message
    
    Gets the error message associated with a particular error code.
    
    Parameters:
        result: the result code to be interpreted
    
    Returns: a string representation of the error message associated with the
    passed error code.
    """
    errmsg = ctypes.create_string_buffer(128)
    canGetErrorText(result, errmsg, len(errmsg))
    return ("%s (code %d)" % (errmsg.value, result))


def _handle_is_valid(handle):
    """
    Method: _handle_is_valid
    
    Used to determine if a handle is valid
    
    Parameters:
        handle: handle to be tested
    
    Returns:
        True if the handle is valid, False if it is not.
    """
    return (handle >= 0)


def _check_bus_handle_validity(handle, function, arguments):
    """
    Method: _check_bus_handle_validity
    
    Utility function called by CANLIB functions that return a bus handle
    to determine validity of the handle. If the passed handle is not valid,
    a CANLIBError exception containing details of the function called and
    arguments passed to the function is thrown.
    
    Parameters:
        handle: the handle returned from the CANLIB function called
        function: the CANLIB function called
        arguments: the arguments passed to the CANLIB function called
    
    Returns:
        The handle being tested, provided it is valid.
    """
    if not _handle_is_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle


def _convert_can_status_to_int(result):
    """
    Method: _convert_can_status_to_int
    
    Ensures that the type of a CAN status return value from a function is
    converted from a ctypes type to a pure Python type.
    
    Parameters:
        result: the status value to be converted
    
    Returns:
        The converted status value (if a conversion was necessary) or the
        original status value (if a conversion was unnecessary).
    """
    if isinstance(result, (types.IntType, types.LongType)):
        _result = result
    else:
        _result = result.value
    return _result


def _check_status(result, function, arguments):
    """
    Method: _check_status
    
    Used to check the return value from CANLIB functions. This version of
    _check_status interprets canERR_NOMSG as an error.
    
    Parameters:
        result: the result returned from the CANLIB function called.
        function: the CANLIB function called.
        arguments: the arguments passed to the CANLIB function called.
    """
    _result = _convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result):
        raise CANLIBError(function, _result, arguments)
    else:
        return result


def _check_status_read(result, function, arguments):
    """
    Method: _check_status_read
    
    Used to check the return value from CANLIB functions. This version of
    _check_status does not interpret canERR_NOMSG as an error.
    
    Parameters:
        result: the result returned from the CANLIB function called.
        function: the CANLIB function called.
        arguments: the arguments passed to the CANLIB function called.
    """
    _result = _convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result) and \
      (_result != canstat.canERR_NOMSG):
        raise CANLIBError(function, _result, arguments)
    else:
        return result


class c_canHandle(ctypes.c_int):
    """
    Class: c_canHandle
    
    Class representing a CAN handle.
    
    Parent class: ctypes.c_int
    """
    pass

canINVALID_HANDLE = -1

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200
FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED |
              canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE |
              canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS |
              canOPEN_ACCEPT_LARGE_DLC)

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

canIOCTL_PREFER_EXT = 1
canIOCTL_PREFER_STD = 2
canIOCTL_CLEAR_ERROR_COUNTERS = 5
canIOCTL_SET_TIMER_SCALE = 6
canIOCTL_SET_TXACK = 7

CANID_METAMSG = (-1L)
CANID_WILDCARD = (-2L)

canInitializeLibrary = _get_canlib().canInitializeLibrary
canInitializeLibrary.argtypes = []

canClose = _get_canlib().canClose
canClose.argtypes = [ctypes.c_int]
canClose.restype = canstat.c_canStatus
canClose.errcheck = _check_status

canBusOn = _get_canlib().canBusOn
canBusOn.argtypes = [ctypes.c_int]
canBusOn.restype = canstat.c_canStatus
canBusOn.errcheck = _check_status

canBusOff = _get_canlib().canBusOff
canBusOff.argtypes = [ctypes.c_int]
canBusOff.restype = canstat.c_canStatus
canBusOff.errcheck = _check_status

canSetBusParams = _get_canlib().canSetBusParams
canSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                            ctypes.c_uint]
canSetBusParams.restype = canstat.c_canStatus
canSetBusParams.errcheck = _check_status

canGetBusParams = _get_canlib().canGetBusParams
canGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p]
canGetBusParams.restype = canstat.c_canStatus
canGetBusParams.errcheck = _check_status

canSetBusOutputControl = _get_canlib().canSetBusOutputControl
canSetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_uint]
canSetBusOutputControl.restype = canstat.c_canStatus
canSetBusOutputControl.errcheck = _check_status

canGetBusOutputControl = _get_canlib().canGetBusOutputControl
canGetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_void_p]
canGetBusOutputControl.restype = canstat.c_canStatus
canGetBusOutputControl.errcheck = _check_status

canAccept = _get_canlib().canAccept
canAccept.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint]
canAccept.restype = canstat.c_canStatus
canAccept.errcheck = _check_status

canReadStatus = _get_canlib().canReadStatus
canReadStatus.argtypes = [ctypes.c_int, ctypes.c_void_p]
canReadStatus.restype = canstat.c_canStatus
canReadStatus.errcheck = _check_status

canReadErrorCounters = _get_canlib().canReadErrorCounters
canReadErrorCounters.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canReadErrorCounters.restype = canstat.c_canStatus
canReadErrorCounters.errcheck = _check_status

canWrite = _get_canlib().canWrite
canWrite.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                     ctypes.c_uint, ctypes.c_uint]
canWrite.restype = canstat.c_canStatus
canWrite.errcheck = _check_status

canWriteSync = _get_canlib().canWriteSync
canWriteSync.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint]
canWriteSync.restype = canstat.c_canStatus
canWriteSync.errcheck = _check_status

canRead = _get_canlib().canRead
canRead.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canRead.restype = canstat.c_canStatus
canRead.errcheck = _check_status_read

canReadWait = _get_canlib().canReadWait
canReadWait.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_long]
canReadWait.restype = canstat.c_canStatus
canReadWait.errcheck = _check_status_read

canReadSpecific = _get_canlib().canReadSpecific
canReadSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canReadSpecific.restype = canstat.c_canStatus
canReadSpecific.errcheck = _check_status_read

canReadSync = _get_canlib().canReadSync
canReadSync.argtypes = [ctypes.c_int, ctypes.c_ulong]
canReadSync.restype = canstat.c_canStatus
canReadSync.errcheck = _check_status_read

canReadSyncSpecific = _get_canlib().canReadSyncSpecific
canReadSyncSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_ulong]
canReadSyncSpecific.restype = canstat.c_canStatus
canReadSyncSpecific.errcheck = _check_status_read

canReadSpecificSkip = _get_canlib().canReadSpecificSkip
canReadSpecificSkip.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_void_p, ctypes.c_void_p,
                                ctypes.c_void_p]
canReadSpecificSkip.restype = canstat.c_canStatus
canReadSpecificSkip.errcheck = _check_status_read

canSetNotify = _get_canlib().canSetNotify
canSetNotify.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
canSetNotify.restype = canstat.c_canStatus
canSetNotify.errcheck = _check_status

canTranslateBaud = _get_canlib().canTranslateBaud
canTranslateBaud.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p]
canTranslateBaud.restype = canstat.c_canStatus
canTranslateBaud.errcheck = _check_status

canGetErrorText = _get_canlib().canGetErrorText
canGetErrorText.argtypes = [canstat.c_canStatus, ctypes.c_char_p,
                            ctypes.c_uint]
canGetErrorText.restype = canstat.c_canStatus
canGetErrorText.errcheck = _check_status

canGetVersion = _get_canlib().canGetVersion
canGetVersion.argtypes = []
canGetVersion.restype = ctypes.c_ushort
#canGetVersion doesn't return a canstat.c_canStatus value, so it has no error
#checking

canIoCtl = _get_canlib().canIoCtl
canIoCtl.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
                     ctypes.c_uint]
canIoCtl.restype = canstat.c_canStatus
canIoCtl.errcheck = _check_status

canReadTimer = _get_canlib().canReadTimer
canReadTimer.argtypes = [ctypes.c_int]
canReadTimer.restype = ctypes.c_ulong
canReadTimer.errcheck = _check_status

canOpenChannel = _get_canlib().canOpenChannel
canOpenChannel.argtypes = [ctypes.c_int, ctypes.c_int]
canOpenChannel.restype = ctypes.c_int
canOpenChannel.errcheck = _check_bus_handle_validity

canGetNumberOfChannels = _get_canlib().canGetNumberOfChannels
canGetNumberOfChannels.argtypes = [ctypes.c_void_p]
canGetNumberOfChannels.restype = canstat.c_canStatus
canGetNumberOfChannels.errcheck = _check_status

canGetChannelData = _get_canlib().canGetChannelData
canGetChannelData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                              ctypes.c_size_t]
canGetChannelData.restype = canstat.c_canStatus
canGetChannelData.errcheck = _check_status

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


class c_canUserIOPortData(ctypes.Structure):
    """
    Class: c_canUserIOPortData
    
    Representation of the CANLIB canUserIoPortData structure.
    
    Parent class: ctypes.Structure
    """
    _fields_ = [("portNo", ctypes.c_uint), ("portValue", ctypes.c_uint)]

canWaitForEvent = _get_canlib().canWaitForEvent
canWaitForEvent.argtypes = [ctypes.c_int, ctypes.c_ulong]
canWaitForEvent.restype = canstat.c_canStatus
canWaitForEvent.errcheck = _check_status

canSetBusParamsC200 = _get_canlib().canSetBusParamsC200
canSetBusParamsC200.argtypes = [ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte]
canSetBusParamsC200.restype = canstat.c_canStatus
canSetBusParamsC200.errcheck = _check_status

canSetDriverMode = _get_canlib().canSetDriverMode
canSetDriverMode.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
canSetDriverMode.restype = canstat.c_canStatus
canSetDriverMode.errcheck = _check_status

canGetDriverMode = _get_canlib().canGetDriverMode
canGetDriverMode.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
canGetDriverMode.restype = canstat.c_canStatus
canGetDriverMode.errcheck = _check_status

canVERSION_CANLIB32_VERSION = 0
canVERSION_CANLIB32_PRODVER = 1
canVERSION_CANLIB32_PRODVER32 = 2
canVERSION_CANLIB32_BETA = 3

canGetVersionEx = _get_canlib().canGetVersionEx
canGetVersionEx.argtypes = [ctypes.c_uint]
canGetVersionEx.restype = ctypes.c_uint
#canGetVersionEx doesn't return a canstat.c_canStatus value, so it has no
#error checking

canParamGetCount = _get_canlib().canParamGetCount
canParamGetCount.argtypes = []
canParamGetCount.restype = canstat.c_canStatus
canParamGetCount.errcheck = _check_status

canParamCommitChanges = _get_canlib().canParamCommitChanges
canParamCommitChanges.argtypes = []
canParamCommitChanges.restype = canstat.c_canStatus
canParamCommitChanges.errcheck = _check_status

canParamDeleteEntry = _get_canlib().canParamDeleteEntry
canParamDeleteEntry.argtypes = [ctypes.c_int]
canParamDeleteEntry.restype = canstat.c_canStatus
canParamDeleteEntry.errcheck = _check_status

canParamCreateNewEntry = _get_canlib().canParamCreateNewEntry
canParamCreateNewEntry.argtypes = []
canParamCreateNewEntry.restype = canstat.c_canStatus
canParamCreateNewEntry.errcheck = _check_status

canParamSwapEntries = _get_canlib().canParamSwapEntries
canParamSwapEntries.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSwapEntries.restype = canstat.c_canStatus
canParamSwapEntries.errcheck = _check_status

canParamGetName = _get_canlib().canParamGetName
canParamGetName.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
canParamGetName.restype = canstat.c_canStatus
canParamGetName.errcheck = _check_status


canParamGetChannelNumber = _get_canlib().canParamGetChannelNumber
canParamGetChannelNumber.argtypes = [ctypes.c_int]
canParamGetChannelNumber.restype = canstat.c_canStatus
canParamGetChannelNumber.errcheck = _check_status

canParamGetBusParams = _get_canlib().canParamGetBusParams
canParamGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canParamGetBusParams.restype = canstat.c_canStatus
canParamGetBusParams.errcheck = _check_status

canParamSetName = _get_canlib().canParamSetName
canParamSetName.argtypes = [ctypes.c_int, ctypes.c_char_p]
canParamSetName.restype = canstat.c_canStatus
canParamSetName.errcheck = _check_status

canParamSetChannelNumber = _get_canlib().canParamSetChannelNumber
canParamSetChannelNumber.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSetChannelNumber.restype = canstat.c_canStatus
canParamSetChannelNumber.errcheck = _check_status

canParamSetBusParams = _get_canlib().canParamSetBusParams
canParamSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                                 ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
canParamSetBusParams.restype = canstat.c_canStatus
canParamSetBusParams.errcheck = _check_status

canParamFindByName = _get_canlib().canParamFindByName
canParamFindByName.argtypes = [ctypes.c_char_p]
canParamFindByName.restype = canstat.c_canStatus
canParamFindByName.errcheck = _check_status

canObjBufFreeAll = _get_canlib().canObjBufFreeAll
canObjBufFreeAll.argtypes = [ctypes.c_int]
canObjBufFreeAll.restype = canstat.c_canStatus
canObjBufFreeAll.errcheck = _check_status

canObjBufAllocate = _get_canlib().canObjBufAllocate
canObjBufAllocate.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufAllocate.restype = canstat.c_canStatus
canObjBufAllocate.errcheck = _check_status

canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

canObjBufFree = _get_canlib().canObjBufFree
canObjBufFree.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufFree.restype = canstat.c_canStatus
canObjBufFree.errcheck = _check_status

canObjBufWrite = _get_canlib().canObjBufWrite
canObjBufWrite.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
canObjBufWrite.restype = canstat.c_canStatus
canObjBufWrite.errcheck = _check_status

canObjBufSetFilter = _get_canlib().canObjBufSetFilter
canObjBufSetFilter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                               ctypes.c_uint]
canObjBufSetFilter.restype = canstat.c_canStatus
canObjBufSetFilter.errcheck = _check_status

canObjBufSetFlags = _get_canlib().canObjBufSetFlags
canObjBufSetFlags.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetFlags.restype = canstat.c_canStatus
canObjBufSetFlags.errcheck = _check_status

canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

canObjBufSetPeriod = _get_canlib().canObjBufSetPeriod
canObjBufSetPeriod.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetPeriod.restype = canstat.c_canStatus
canObjBufSetPeriod.errcheck = _check_status

canObjBufSetMsgCount = _get_canlib().canObjBufSetMsgCount
canObjBufSetMsgCount.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetMsgCount.restype = canstat.c_canStatus
canObjBufSetMsgCount.errcheck = _check_status

canObjBufEnable = _get_canlib().canObjBufEnable
canObjBufEnable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufEnable.restype = canstat.c_canStatus
canObjBufEnable.errcheck = _check_status

canObjBufDisable = _get_canlib().canObjBufDisable
canObjBufDisable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufDisable.restype = canstat.c_canStatus
canObjBufDisable.errcheck = _check_status

canObjBufSendBurst = _get_canlib().canObjBufSendBurst
canObjBufSendBurst.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSendBurst.restype = canstat.c_canStatus
canObjBufSendBurst.errcheck = _check_status

canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

canProbeVersion = _get_canlib().canProbeVersion
canProbeVersion.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_int, ctypes.c_uint]
canProbeVersion.restype = ctypes.c_bool
#canProbeVersion doesn't return a canstat.c_canStatus value, so it has no
#error checking

canResetBus = _get_canlib().canResetBus
canResetBus.argtypes = [ctypes.c_int]
canResetBus.restype = canstat.c_canStatus
canResetBus.errcheck = _check_status

canWriteWait = _get_canlib().canWriteWait
canWriteWait.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong]
canWriteWait.restype = canstat.c_canStatus
canWriteWait.errcheck = _check_status

canUnloadLibrary = _get_canlib().canUnloadLibrary
canUnloadLibrary.argtypes = []
canUnloadLibrary.restype = canstat.c_canStatus
canUnloadLibrary.errcheck = _check_status

ACCEPTANCE_FILTER_TYPE_STD = 0
ACCEPTANCE_FILTER_TYPE_EXT = 1

canSetAcceptanceFilter = _get_canlib().canSetAcceptanceFilter
canSetAcceptanceFilter.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
                                   ctypes.c_int]
canSetAcceptanceFilter.restype = canstat.c_canStatus
canSetAcceptanceFilter.errcheck = _check_status

canFlushReceiveQueue = _get_canlib().canFlushReceiveQueue
canFlushReceiveQueue.argtypes = [ctypes.c_int]
canFlushReceiveQueue.restype = canstat.c_canStatus
canFlushReceiveQueue.errcheck = _check_status

canFlushTransmitQueue = _get_canlib().canFlushTransmitQueue
canFlushTransmitQueue.argtypes = [ctypes.c_int]
canFlushTransmitQueue.restype = canstat.c_canStatus
canFlushTransmitQueue.errcheck = _check_status

kvGetApplicationMapping = _get_canlib().kvGetApplicationMapping
kvGetApplicationMapping.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                    ctypes.c_int, ctypes.c_void_p]
kvGetApplicationMapping.restype = canstat.c_canStatus
kvGetApplicationMapping.errcheck = _check_status

kvBeep = _get_canlib().kvBeep
kvBeep.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
kvBeep.restype = canstat.c_canStatus
kvBeep.errcheck = _check_status

kvSelfTest = _get_canlib().kvSelfTest
kvSelfTest.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvSelfTest.restype = canstat.c_canStatus
kvSelfTest.errcheck = _check_status

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

kvFlashLeds = _get_canlib().kvFlashLeds
kvFlashLeds.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
kvFlashLeds.restype = canstat.c_canStatus
kvFlashLeds.errcheck = _check_status

canRequestChipStatus = _get_canlib().canRequestChipStatus
canRequestChipStatus.argtypes = [ctypes.c_int]
canRequestChipStatus.restype = canstat.c_canStatus
canRequestChipStatus.errcheck = _check_status

canRequestBusStatistics = _get_canlib().canRequestBusStatistics
canRequestBusStatistics.argtypes = [ctypes.c_int]
canRequestBusStatistics.restype = canstat.c_canStatus
canRequestBusStatistics.errcheck = _check_status


class c_canBusStatistics(ctypes.Structure):
    """
    Class: c_canBusStatistics
    
    Representation of the CANLIB canBusStatistics class.
    
    Parent class: ctypes.Structure
    """
    _fields_ = [("std_data", ctypes.c_ulong), ("std_remote", ctypes.c_ulong),
      ("ext_data", ctypes.c_ulong), ("ext_remote", ctypes.c_ulong),
      ("error_frames", ctypes.c_ulong), ("bus_load", ctypes.c_ulong),
      ("overruns", ctypes.c_ulong)]

canGetBusStatistics = _get_canlib().canGetBusStatistics
canGetBusStatistics.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
canGetBusStatistics.restype = canstat.c_canStatus
canGetBusStatistics.errcheck = _check_status

canSetBitrate = _get_canlib().canSetBitrate
canSetBitrate.argtypes = [ctypes.c_int, ctypes.c_int]
canSetBitrate.restype = canstat.c_canStatus
canSetBitrate.errcheck = _check_status

kvAnnounceIdentity = _get_canlib().kvAnnounceIdentity
kvAnnounceIdentity.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
kvAnnounceIdentity.restype = canstat.c_canStatus
kvAnnounceIdentity.errcheck = _check_status

canGetHandleData = _get_canlib().canGetHandleData
canGetHandleData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                             ctypes.c_size_t]
canGetHandleData.restype = canstat.c_canStatus
canGetHandleData.errcheck = _check_status


class c_kvTimeDomain(ctypes.c_void_p):
    """
    Class: c_kvTimeDomain
    
    Representation of CANLIB's kvTimeDomain class
    
    Parent class: ctypes.c_void_p
    """
    pass


class c_kvStatus(canstat.c_canStatus):
    """
    Class: c_kvStatus
    
    Representation of CANLIB's kvStatus class
    
    Parent class: canstat.c_canStatus
    """
    pass


class c_kvTimeDomainData(ctypes.Structure):
    """
    Class: c_kvTimeDomainData
    
    Representation of CANLIB's kvTimeDomainData class
    
    Parent class: ctypes.Structure
    """
    _fields_ = [("nMagiSyncGroups", ctypes.c_int),
                ("nMagiSyncedMembers", ctypes.c_int),
                ("nNonMagiSyncCards", ctypes.c_int),
                ("nNonMagiSyncedMembers", ctypes.c_int)]

kvTimeDomainCreate = _get_canlib().kvTimeDomainCreate
kvTimeDomainCreate.argtypes = [c_kvTimeDomain]
kvTimeDomainCreate.restype = c_kvStatus
kvTimeDomainCreate.errcheck = _check_status

kvTimeDomainDelete = _get_canlib().kvTimeDomainDelete
kvTimeDomainDelete.argtypes = [c_kvTimeDomain]
kvTimeDomainDelete.restype = c_kvStatus
kvTimeDomainDelete.errcheck = _check_status

kvTimeDomainResetTime = _get_canlib().kvTimeDomainResetTime
kvTimeDomainResetTime.argtypes = [c_kvTimeDomain]
kvTimeDomainResetTime.restype = c_kvStatus
kvTimeDomainResetTime.errcheck = _check_status

kvTimeDomainGetData = _get_canlib().kvTimeDomainGetData
kvTimeDomainGetData.argtypes = [c_kvTimeDomain, ctypes.c_void_p,
                                ctypes.c_size_t]
kvTimeDomainGetData.restype = c_kvStatus
kvTimeDomainGetData.errcheck = _check_status

kvTimeDomainAddHandle = _get_canlib().kvTimeDomainAddHandle
kvTimeDomainAddHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainAddHandle.restype = c_kvStatus
kvTimeDomainAddHandle.errcheck = _check_status

kvTimeDomainRemoveHandle = _get_canlib().kvTimeDomainRemoveHandle
kvTimeDomainRemoveHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainRemoveHandle.restype = c_kvStatus
kvTimeDomainRemoveHandle.errcheck = _check_status


class c_kvCallback(ctypes.c_void_p):
    """
    Class: c_kvCallback
    
    Representation of CANLIB's kvCallback class
    
    Parent class: ctypes.c_void_p
    """
    pass

CALLBACKFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
NULL_CALLBACK = ctypes.cast(None, CALLBACKFUNC)


kvSetNotifyCallback = _get_canlib().kvSetNotifyCallback
kvSetNotifyCallback.argtypes = [ctypes.c_int, c_kvCallback, ctypes.c_void_p,
                                ctypes.c_uint]
kvSetNotifyCallback.restype = c_kvStatus
kvSetNotifyCallback.errcheck = _check_status

kvBUSTYPE_NONE = 0
kvBUSTYPE_PCI = 1
kvBUSTYPE_PCMCIA = 2
kvBUSTYPE_USB = 3
kvBUSTYPE_WLAN = 4
kvBUSTYPE_PCI_EXPRESS = 5
kvBUSTYPE_ISA = 6
kvBUSTYPE_VIRTUAL = 7
kvBUSTYPE_PC104_PLUS = 8

kvGetSupportedInterfaceInfo = _get_canlib().kvGetSupportedInterfaceInfo
kvGetSupportedInterfaceInfo.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                        ctypes.c_int, ctypes.c_void_p,
                                        ctypes.c_void_p]
kvGetSupportedInterfaceInfo.restype = c_kvStatus
kvGetSupportedInterfaceInfo.errcheck = _check_status

kvReadTimer = _get_canlib().kvReadTimer
kvReadTimer.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer.restype = c_kvStatus
kvReadTimer.errcheck = _check_status

kvReadTimer64 = _get_canlib().kvReadTimer64
kvReadTimer64.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer64.restype = c_kvStatus
kvReadTimer64.errcheck = _check_status

kvReadDeviceCustomerData = _get_canlib().kvReadDeviceCustomerData
kvReadDeviceCustomerData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_void_p, ctypes.c_size_t]
kvReadDeviceCustomerData.restype = c_kvStatus
kvReadDeviceCustomerData.errcheck = _check_status

ENVVAR_TYPE_INT = 1
ENVVAR_TYPE_FLOAT = 2
ENVVAR_TYPE_STRING = 3


class c_kvEnvHandle(ctypes.c_longlong):
    """
    Class: c_kvEnvHandle
    
    Representation of CANLIB's kvEnvHandle class
    
    Parent class: ctypes.c_longlong
    """
    pass

kvScriptStart = _get_canlib().kvScriptStart
kvScriptStart.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStart.restype = c_kvStatus
kvScriptStart.errcheck = _check_status

kvScriptStop = _get_canlib().kvScriptStop
kvScriptStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStop.restype = c_kvStatus
kvScriptStop.errcheck = _check_status

kvScriptForceStop = _get_canlib().kvScriptForceStop
kvScriptForceStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptForceStop.restype = c_kvStatus
kvScriptForceStop.errcheck = _check_status

kvScriptSendEvent = _get_canlib().kvScriptSendEvent
kvScriptSendEvent.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int]
kvScriptSendEvent.restype = c_kvStatus
kvScriptSendEvent.errcheck = _check_status

kvScriptEnvvarOpen = _get_canlib().kvScriptEnvvarOpen
kvScriptEnvvarOpen.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                               ctypes.c_void_p, ctypes.c_void_p]
kvScriptEnvvarOpen.restype = c_kvEnvHandle
#Since kvScriptEnvvarOpen doesn't return a status value, it has no error
#checking

kvScriptEnvvarClose = _get_canlib().kvScriptEnvvarClose
kvScriptEnvvarClose.argtypes = [c_kvEnvHandle]
kvScriptEnvvarClose.restype = c_kvStatus
kvScriptEnvvarClose.errcheck = _check_status

kvScriptEnvvarSetInt = _get_canlib().kvScriptEnvvarSetInt
kvScriptEnvvarSetInt.argtypes = [c_kvEnvHandle, ctypes.c_int]
kvScriptEnvvarSetInt.restype = c_kvStatus
kvScriptEnvvarSetInt.errcheck = _check_status

kvScriptEnvvarGetInt = _get_canlib().kvScriptEnvvarGetInt
kvScriptEnvvarGetInt.argtypes = [c_kvEnvHandle, ctypes.c_void_p]
kvScriptEnvvarGetInt.restype = c_kvStatus
kvScriptEnvvarGetInt.errcheck = _check_status

kvScriptEnvvarSetData = _get_canlib().kvScriptEnvvarSetData
kvScriptEnvvarSetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarSetData.restype = c_kvStatus
kvScriptEnvvarSetData.errcheck = _check_status

kvScriptEnvvarGetData = _get_canlib().kvScriptEnvvarGetData
kvScriptEnvvarGetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarGetData.restype = c_kvStatus
kvScriptEnvvarGetData.errcheck = _check_status

kvScriptGetMaxEnvvarSize = _get_canlib().kvScriptGetMaxEnvvarSize
kvScriptGetMaxEnvvarSize.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvScriptGetMaxEnvvarSize.restype = c_kvStatus
kvScriptGetMaxEnvvarSize.errcheck = _check_status

kvScriptLoadFileOnDevice = _get_canlib().kvScriptLoadFileOnDevice
kvScriptLoadFileOnDevice.argtypes = [ctypes.c_int, ctypes.c_int,
                                     ctypes.c_char_p]
kvScriptLoadFileOnDevice.restype = c_kvStatus
kvScriptLoadFileOnDevice.errcheck = _check_status

kvScriptLoadFile = _get_canlib().kvScriptLoadFile
kvScriptLoadFile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvScriptLoadFile.restype = c_kvStatus
kvScriptLoadFile.errcheck = _check_status

kvFileCopyToDevice = _get_canlib().kvFileCopyToDevice
kvFileCopyToDevice.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvFileCopyToDevice.restype = c_kvStatus
kvFileCopyToDevice.errcheck = _check_status

kvFileCopyFromDevice = _get_canlib().kvFileCopyFromDevice
kvFileCopyFromDevice.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                 ctypes.c_char_p]
kvFileCopyFromDevice.restype = c_kvStatus
kvFileCopyFromDevice.errcheck = _check_status

kvFileDelete = _get_canlib().kvFileDelete
kvFileDelete.argtypes = [ctypes.c_int, ctypes.c_char_p]
kvFileDelete.restype = c_kvStatus
kvFileDelete.errcheck = _check_status

kvFileGetSystemData = _get_canlib().kvFileGetSystemData
kvFileGetSystemData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
kvFileGetSystemData.restype = c_kvStatus
kvFileGetSystemData.errcheck = _check_status

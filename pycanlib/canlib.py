import ctypes
import sys

import CANLIBErrorHandlers
import canstat

canlibDict = {"win32": (ctypes.WinDLL, "canlib32.dll"),
              "posix": (ctypes.CDLL, "libcanlib.so")}

libraryConstructor = canlibDict[sys.platform][0]
libraryName = canlibDict[sys.platform][1]
canlib32 = libraryConstructor(libraryName)


class c_canHandle(ctypes.c_int):
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

canInitializeLibrary = canlib32.canInitializeLibrary
canInitializeLibrary.argtypes = []

canClose = canlib32.canClose
canClose.argtypes = [ctypes.c_int]
canClose.restype = canstat.c_canStatus
canClose.errcheck = CANLIBErrorHandlers.CheckStatus

canBusOn = canlib32.canBusOn
canBusOn.argtypes = [ctypes.c_int]
canBusOn.restype = canstat.c_canStatus
canBusOn.errcheck = CANLIBErrorHandlers.CheckStatus

canBusOff = canlib32.canBusOff
canBusOff.argtypes = [ctypes.c_int]
canBusOff.restype = canstat.c_canStatus
canBusOff.errcheck = CANLIBErrorHandlers.CheckStatus

canSetBusParams = canlib32.canSetBusParams
canSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                            ctypes.c_uint]
canSetBusParams.restype = canstat.c_canStatus
canSetBusParams.errcheck = CANLIBErrorHandlers.CheckStatus

canGetBusParams = canlib32.canGetBusParams
canGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p]
canGetBusParams.restype = canstat.c_canStatus
canGetBusParams.errcheck = CANLIBErrorHandlers.CheckStatus

canSetBusOutputControl = canlib32.canSetBusOutputControl
canSetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_uint]
canSetBusOutputControl.restype = canstat.c_canStatus
canSetBusOutputControl.errcheck = CANLIBErrorHandlers.CheckStatus

canGetBusOutputControl = canlib32.canGetBusOutputControl
canGetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_void_p]
canGetBusOutputControl.restype = canstat.c_canStatus
canGetBusOutputControl.errcheck = CANLIBErrorHandlers.CheckStatus

canAccept = canlib32.canAccept
canAccept.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint]
canAccept.restype = canstat.c_canStatus
canAccept.errcheck = CANLIBErrorHandlers.CheckStatus

canReadStatus = canlib32.canReadStatus
canReadStatus.argtypes = [ctypes.c_int, ctypes.c_void_p]
canReadStatus.restype = canstat.c_canStatus
canReadStatus.errcheck = CANLIBErrorHandlers.CheckStatus

canReadErrorCounters = canlib32.canReadErrorCounters
canReadErrorCounters.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canReadErrorCounters.restype = canstat.c_canStatus
canReadErrorCounters.errcheck = CANLIBErrorHandlers.CheckStatus

canWrite = canlib32.canWrite
canWrite.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                     ctypes.c_uint, ctypes.c_uint]
canWrite.restype = canstat.c_canStatus
canWrite.errcheck = CANLIBErrorHandlers.CheckStatus

canWriteSync = canlib32.canWriteSync
canWriteSync.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint]
canWriteSync.restype = canstat.c_canStatus
canWriteSync.errcheck = CANLIBErrorHandlers.CheckStatus

canRead = canlib32.canRead
canRead.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canRead.restype = canstat.c_canStatus
canRead.errcheck = CANLIBErrorHandlers.CheckStatus

canReadWait = canlib32.canReadWait
canReadWait.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_long]
canReadWait.restype = canstat.c_canStatus
canReadWait.errcheck = CANLIBErrorHandlers.CheckStatus

canReadSpecific = canlib32.canReadSpecific
canReadSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canReadSpecific.restype = canstat.c_canStatus
canReadSpecific.errcheck = CANLIBErrorHandlers.CheckStatus

canReadSync = canlib32.canReadSync
canReadSync.argtypes = [ctypes.c_int, ctypes.c_ulong]
canReadSync.restype = canstat.c_canStatus
canReadSync.errcheck = CANLIBErrorHandlers.CheckStatus

canReadSyncSpecific = canlib32.canReadSyncSpecific
canReadSyncSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_ulong]
canReadSyncSpecific.restype = canstat.c_canStatus
canReadSyncSpecific.errcheck = CANLIBErrorHandlers.CheckStatus

canReadSpecificSkip = canlib32.canReadSpecificSkip
canReadSpecificSkip.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_void_p, ctypes.c_void_p,
                                ctypes.c_void_p]
canReadSpecificSkip.restype = canstat.c_canStatus
canReadSpecificSkip.errcheck = CANLIBErrorHandlers.CheckStatus

canSetNotify = canlib32.canSetNotify
canSetNotify.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
canSetNotify.restype = canstat.c_canStatus
canSetNotify.errcheck = CANLIBErrorHandlers.CheckStatus

canTranslateBaud = canlib32.canTranslateBaud
canTranslateBaud.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p]
canTranslateBaud.restype = canstat.c_canStatus
canTranslateBaud.errcheck = CANLIBErrorHandlers.CheckStatus

canGetErrorText = canlib32.canGetErrorText
canGetErrorText.argtypes = [canstat.c_canStatus, ctypes.c_char_p,
                            ctypes.c_uint]
canGetErrorText.restype = canstat.c_canStatus
canGetErrorText.errcheck = CANLIBErrorHandlers.CheckStatus

canGetVersion = canlib32.canGetVersion
canGetVersion.argtypes = []
canGetVersion.restype = ctypes.c_ushort
#canGetVersion doesn't return a canstat.c_canStatus value, so it has no error
#checking

canIoCtl = canlib32.canIoCtl
canIoCtl.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
                     ctypes.c_uint]
canIoCtl.restype = canstat.c_canStatus
canIoCtl.errcheck = CANLIBErrorHandlers.CheckStatus

canReadTimer = canlib32.canReadTimer
canReadTimer.argtypes = [ctypes.c_int]
canReadTimer.restype = ctypes.c_ulong
#canReadTimer doesn't return a canstat.c_canStatus value, so it has no error
#checking

canOpenChannel = canlib32.canOpenChannel
canOpenChannel.argtypes = [ctypes.c_int, ctypes.c_int]
canOpenChannel.restype = ctypes.c_int
canOpenChannel.errcheck = CANLIBErrorHandlers.CheckBusHandleValidity

canGetNumberOfChannels = canlib32.canGetNumberOfChannels
canGetNumberOfChannels.argtypes = [ctypes.c_void_p]
canGetNumberOfChannels.restype = canstat.c_canStatus
canGetNumberOfChannels.errcheck = CANLIBErrorHandlers.CheckStatus

canGetChannelData = canlib32.canGetChannelData
canGetChannelData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                              ctypes.c_size_t]
canGetChannelData.restype = canstat.c_canStatus
canGetChannelData.errcheck = CANLIBErrorHandlers.CheckStatus

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
    _fields_ = [("portNo", ctypes.c_uint), ("portValue", ctypes.c_uint)]

canWaitForEvent = canlib32.canWaitForEvent
canWaitForEvent.argtypes = [ctypes.c_int, ctypes.c_ulong]
canWaitForEvent.restype = canstat.c_canStatus
canWaitForEvent.errcheck = CANLIBErrorHandlers.CheckStatus

canSetBusParamsC200 = canlib32.canSetBusParamsC200
canSetBusParamsC200.argtypes = [ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte]
canSetBusParamsC200.restype = canstat.c_canStatus
canSetBusParamsC200.errcheck = CANLIBErrorHandlers.CheckStatus

canSetDriverMode = canlib32.canSetDriverMode
canSetDriverMode.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
canSetDriverMode.restype = canstat.c_canStatus
canSetDriverMode.errcheck = CANLIBErrorHandlers.CheckStatus

canGetDriverMode = canlib32.canGetDriverMode
canGetDriverMode.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
canGetDriverMode.restype = canstat.c_canStatus
canGetDriverMode.errcheck = CANLIBErrorHandlers.CheckStatus

canVERSION_CANLIB32_VERSION = 0
canVERSION_CANLIB32_PRODVER = 1
canVERSION_CANLIB32_PRODVER32 = 2
canVERSION_CANLIB32_BETA = 3

canGetVersionEx = canlib32.canGetVersionEx
canGetVersionEx.argtypes = [ctypes.c_uint]
canGetVersionEx.restype = ctypes.c_uint
#canGetVersionEx doesn't return a canstat.c_canStatus value, so it has no
#error checking

canParamGetCount = canlib32.canParamGetCount
canParamGetCount.argtypes = []
canParamGetCount.restype = canstat.c_canStatus
canParamGetCount.errcheck = CANLIBErrorHandlers.CheckStatus

canParamCommitChanges = canlib32.canParamCommitChanges
canParamCommitChanges.argtypes = []
canParamCommitChanges.restype = canstat.c_canStatus
canParamCommitChanges.errcheck = CANLIBErrorHandlers.CheckStatus

canParamDeleteEntry = canlib32.canParamDeleteEntry
canParamDeleteEntry.argtypes = [ctypes.c_int]
canParamDeleteEntry.restype = canstat.c_canStatus
canParamDeleteEntry.errcheck = CANLIBErrorHandlers.CheckStatus

canParamCreateNewEntry = canlib32.canParamCreateNewEntry
canParamCreateNewEntry.argtypes = []
canParamCreateNewEntry.restype = canstat.c_canStatus
canParamCreateNewEntry.errcheck = CANLIBErrorHandlers.CheckStatus

canParamSwapEntries = canlib32.canParamSwapEntries
canParamSwapEntries.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSwapEntries.restype = canstat.c_canStatus
canParamSwapEntries.errcheck = CANLIBErrorHandlers.CheckStatus

canParamGetName = canlib32.canParamGetName
canParamGetName.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
canParamGetName.restype = canstat.c_canStatus
canParamGetName.errcheck = CANLIBErrorHandlers.CheckStatus


canParamGetChannelNumber = canlib32.canParamGetChannelNumber
canParamGetChannelNumber.argtypes = [ctypes.c_int]
canParamGetChannelNumber.restype = canstat.c_canStatus
canParamGetChannelNumber.errcheck = CANLIBErrorHandlers.CheckStatus

canParamGetBusParams = canlib32.canParamGetBusParams
canParamGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canParamGetBusParams.restype = canstat.c_canStatus
canParamGetBusParams.errcheck = CANLIBErrorHandlers.CheckStatus

canParamSetName = canlib32.canParamSetName
canParamSetName.argtypes = [ctypes.c_int, ctypes.c_char_p]
canParamSetName.restype = canstat.c_canStatus
canParamSetName.errcheck = CANLIBErrorHandlers.CheckStatus

canParamSetChannelNumber = canlib32.canParamSetChannelNumber
canParamSetChannelNumber.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSetChannelNumber.restype = canstat.c_canStatus
canParamSetChannelNumber.errcheck = CANLIBErrorHandlers.CheckStatus

canParamSetBusParams = canlib32.canParamSetBusParams
canParamSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                                 ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
canParamSetBusParams.restype = canstat.c_canStatus
canParamSetBusParams.errcheck = CANLIBErrorHandlers.CheckStatus

canParamFindByName = canlib32.canParamFindByName
canParamFindByName.argtypes = [ctypes.c_char_p]
canParamFindByName.restype = canstat.c_canStatus
canParamFindByName.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufFreeAll = canlib32.canObjBufFreeAll
canObjBufFreeAll.argtypes = [ctypes.c_int]
canObjBufFreeAll.restype = canstat.c_canStatus
canObjBufFreeAll.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufAllocate = canlib32.canObjBufAllocate
canObjBufAllocate.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufAllocate.restype = canstat.c_canStatus
canObjBufAllocate.errcheck = CANLIBErrorHandlers.CheckStatus

canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

canObjBufFree = canlib32.canObjBufFree
canObjBufFree.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufFree.restype = canstat.c_canStatus
canObjBufFree.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufWrite = canlib32.canObjBufWrite
canObjBufWrite.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
canObjBufWrite.restype = canstat.c_canStatus
canObjBufWrite.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetFilter = canlib32.canObjBufSetFilter
canObjBufSetFilter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                               ctypes.c_uint]
canObjBufSetFilter.restype = canstat.c_canStatus
canObjBufSetFilter.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetFlags = canlib32.canObjBufSetFlags
canObjBufSetFlags.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetFlags.restype = canstat.c_canStatus
canObjBufSetFlags.errcheck = CANLIBErrorHandlers.CheckStatus

canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

canObjBufSetPeriod = canlib32.canObjBufSetPeriod
canObjBufSetPeriod.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetPeriod.restype = canstat.c_canStatus
canObjBufSetPeriod.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetMsgCount = canlib32.canObjBufSetMsgCount
canObjBufSetMsgCount.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetMsgCount.restype = canstat.c_canStatus
canObjBufSetMsgCount.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufEnable = canlib32.canObjBufEnable
canObjBufEnable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufEnable.restype = canstat.c_canStatus
canObjBufEnable.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufDisable = canlib32.canObjBufDisable
canObjBufDisable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufDisable.restype = canstat.c_canStatus
canObjBufDisable.errcheck = CANLIBErrorHandlers.CheckStatus

canObjBufSendBurst = canlib32.canObjBufSendBurst
canObjBufSendBurst.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSendBurst.restype = canstat.c_canStatus
canObjBufSendBurst.errcheck = CANLIBErrorHandlers.CheckStatus

canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

canProbeVersion = canlib32.canProbeVersion
canProbeVersion.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_int, ctypes.c_uint]
canProbeVersion.restype = ctypes.c_bool
#canProbeVersion doesn't return a canstat.c_canStatus value, so it has no
#error checking

canResetBus = canlib32.canResetBus
canResetBus.argtypes = [ctypes.c_int]
canResetBus.restype = canstat.c_canStatus
canResetBus.errcheck = CANLIBErrorHandlers.CheckStatus

canWriteWait = canlib32.canWriteWait
canWriteWait.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong]
canWriteWait.restype = canstat.c_canStatus
canWriteWait.errcheck = CANLIBErrorHandlers.CheckStatus

canUnloadLibrary = canlib32.canUnloadLibrary
canUnloadLibrary.argtypes = []
canUnloadLibrary.restype = canstat.c_canStatus
canUnloadLibrary.errcheck = CANLIBErrorHandlers.CheckStatus

canSetAcceptanceFilter = canlib32.canSetAcceptanceFilter
canSetAcceptanceFilter.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
                                   ctypes.c_int]
canSetAcceptanceFilter.restype = canstat.c_canStatus
canSetAcceptanceFilter.errcheck = CANLIBErrorHandlers.CheckStatus

canFlushReceiveQueue = canlib32.canFlushReceiveQueue
canFlushReceiveQueue.argtypes = [ctypes.c_int]
canFlushReceiveQueue.restype = canstat.c_canStatus
canFlushReceiveQueue.errcheck = CANLIBErrorHandlers.CheckStatus

canFlushTransmitQueue = canlib32.canFlushTransmitQueue
canFlushTransmitQueue.argtypes = [ctypes.c_int]
canFlushTransmitQueue.restype = canstat.c_canStatus
canFlushTransmitQueue.errcheck = CANLIBErrorHandlers.CheckStatus

kvGetApplicationMapping = canlib32.kvGetApplicationMapping
kvGetApplicationMapping.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                    ctypes.c_int, ctypes.c_void_p]
kvGetApplicationMapping.restype = canstat.c_canStatus
kvGetApplicationMapping.errcheck = CANLIBErrorHandlers.CheckStatus

kvBeep = canlib32.kvBeep
kvBeep.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
kvBeep.restype = canstat.c_canStatus
kvBeep.errcheck = CANLIBErrorHandlers.CheckStatus

kvSelfTest = canlib32.kvSelfTest
kvSelfTest.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvSelfTest.restype = canstat.c_canStatus
kvSelfTest.errcheck = CANLIBErrorHandlers.CheckStatus

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

kvFlashLeds = canlib32.kvFlashLeds
kvFlashLeds.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
kvFlashLeds.restype = canstat.c_canStatus
kvFlashLeds.errcheck = CANLIBErrorHandlers.CheckStatus

canRequestChipStatus = canlib32.canRequestChipStatus
canRequestChipStatus.argtypes = [ctypes.c_int]
canRequestChipStatus.restype = canstat.c_canStatus
canRequestChipStatus.errcheck = CANLIBErrorHandlers.CheckStatus

canRequestBusStatistics = canlib32.canRequestBusStatistics
canRequestBusStatistics.argtypes = [ctypes.c_int]
canRequestBusStatistics.restype = canstat.c_canStatus
canRequestBusStatistics.errcheck = CANLIBErrorHandlers.CheckStatus


class c_canBusStatistics(ctypes.Structure):
    _fields_ = [("stdData", ctypes.c_ulong), ("stdRemote", ctypes.c_ulong),
      ("extData", ctypes.c_ulong), ("extRemote", ctypes.c_ulong),
      ("errFrame", ctypes.c_ulong), ("busLoad", ctypes.c_ulong),
      ("overruns", ctypes.c_ulong)]

canGetBusStatistics = canlib32.canGetBusStatistics
canGetBusStatistics.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
canGetBusStatistics.restype = canstat.c_canStatus
canGetBusStatistics.errcheck = CANLIBErrorHandlers.CheckStatus

canSetBitrate = canlib32.canSetBitrate
canSetBitrate.argtypes = [ctypes.c_int, ctypes.c_int]
canSetBitrate.restype = canstat.c_canStatus
canSetBitrate.errcheck = CANLIBErrorHandlers.CheckStatus

kvAnnounceIdentity = canlib32.kvAnnounceIdentity
kvAnnounceIdentity.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
kvAnnounceIdentity.restype = canstat.c_canStatus
kvAnnounceIdentity.errcheck = CANLIBErrorHandlers.CheckStatus

canGetHandleData = canlib32.canGetHandleData
canGetHandleData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                             ctypes.c_size_t]
canGetHandleData.restype = canstat.c_canStatus
canGetHandleData.errcheck = CANLIBErrorHandlers.CheckStatus


class c_kvTimeDomain(ctypes.c_void_p):
    pass


class c_kvStatus(canstat.c_canStatus):
    pass


class c_kvTimeDomainData(ctypes.Structure):
    _fields_ = [("nMagiSyncGroups", ctypes.c_int),
                ("nMagiSyncedMembers", ctypes.c_int),
                ("nNonMagiSyncCards", ctypes.c_int),
                ("nNonMagiSyncedMembers", ctypes.c_int)]

kvTimeDomainCreate = canlib32.kvTimeDomainCreate
kvTimeDomainCreate.argtypes = [c_kvTimeDomain]
kvTimeDomainCreate.restype = c_kvStatus
kvTimeDomainCreate.errcheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainDelete = canlib32.kvTimeDomainDelete
kvTimeDomainDelete.argtypes = [c_kvTimeDomain]
kvTimeDomainDelete.restype = c_kvStatus
kvTimeDomainDelete.errcheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainResetTime = canlib32.kvTimeDomainResetTime
kvTimeDomainResetTime.argtypes = [c_kvTimeDomain]
kvTimeDomainResetTime.restype = c_kvStatus
kvTimeDomainResetTime.errcheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainGetData = canlib32.kvTimeDomainGetData
kvTimeDomainGetData.argtypes = [c_kvTimeDomain, ctypes.c_void_p,
                                ctypes.c_size_t]
kvTimeDomainGetData.restype = c_kvStatus
kvTimeDomainGetData.errcheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainAddHandle = canlib32.kvTimeDomainAddHandle
kvTimeDomainAddHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainAddHandle.restype = c_kvStatus
kvTimeDomainAddHandle.errcheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainRemoveHandle = canlib32.kvTimeDomainRemoveHandle
kvTimeDomainRemoveHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainRemoveHandle.restype = c_kvStatus
kvTimeDomainRemoveHandle.errcheck = CANLIBErrorHandlers.CheckStatus


class c_kvCallback(ctypes.c_void_p):
    pass

CALLBACKFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
NULL_CALLBACK = ctypes.cast(None, CALLBACKFUNC)

kvSetNotifyCallback = canlib32.kvSetNotifyCallback
kvSetNotifyCallback.argtypes = [ctypes.c_int, c_kvCallback, ctypes.c_void_p,
                                ctypes.c_uint]
kvSetNotifyCallback.restype = c_kvStatus
kvSetNotifyCallback.errcheck = CANLIBErrorHandlers.CheckStatus

kvBUSTYPE_NONE = 0
kvBUSTYPE_PCI = 1
kvBUSTYPE_PCMCIA = 2
kvBUSTYPE_USB = 3
kvBUSTYPE_WLAN = 4
kvBUSTYPE_PCI_EXPRESS = 5
kvBUSTYPE_ISA = 6
kvBUSTYPE_VIRTUAL = 7
kvBUSTYPE_PC104_PLUS = 8

kvGetSupportedInterfaceInfo = canlib32.kvGetSupportedInterfaceInfo
kvGetSupportedInterfaceInfo.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                        ctypes.c_int, ctypes.c_void_p,
                                        ctypes.c_void_p]
kvGetSupportedInterfaceInfo.restype = c_kvStatus
kvGetSupportedInterfaceInfo.errcheck = CANLIBErrorHandlers.CheckStatus

kvReadTimer = canlib32.kvReadTimer
kvReadTimer.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer.restype = c_kvStatus
kvReadTimer.errcheck = CANLIBErrorHandlers.CheckStatus

kvReadTimer64 = canlib32.kvReadTimer64
kvReadTimer64.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer64.restype = c_kvStatus
kvReadTimer64.errcheck = CANLIBErrorHandlers.CheckStatus

kvReadDeviceCustomerData = canlib32.kvReadDeviceCustomerData
kvReadDeviceCustomerData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_void_p, ctypes.c_size_t]
kvReadDeviceCustomerData.restype = c_kvStatus
kvReadDeviceCustomerData.errcheck = CANLIBErrorHandlers.CheckStatus

ENVVAR_TYPE_INT = 1
ENVVAR_TYPE_FLOAT = 2
ENVVAR_TYPE_STRING = 3


class c_kvEnvHandle(ctypes.c_longlong):
    pass

kvScriptStart = canlib32.kvScriptStart
kvScriptStart.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStart.restype = c_kvStatus
kvScriptStart.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptStop = canlib32.kvScriptStop
kvScriptStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStop.restype = c_kvStatus
kvScriptStop.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptForceStop = canlib32.kvScriptForceStop
kvScriptForceStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptForceStop.restype = c_kvStatus
kvScriptForceStop.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptSendEvent = canlib32.kvScriptSendEvent
kvScriptSendEvent.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int]
kvScriptSendEvent.restype = c_kvStatus
kvScriptSendEvent.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarOpen = canlib32.kvScriptEnvvarOpen
kvScriptEnvvarOpen.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                               ctypes.c_void_p, ctypes.c_void_p]
kvScriptEnvvarOpen.restype = c_kvEnvHandle
#Since kvScriptEnvvarOpen doesn't return a status value, it has no error
#checking

kvScriptEnvvarClose = canlib32.kvScriptEnvvarClose
kvScriptEnvvarClose.argtypes = [c_kvEnvHandle]
kvScriptEnvvarClose.restype = c_kvStatus
kvScriptEnvvarClose.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarSetInt = canlib32.kvScriptEnvvarSetInt
kvScriptEnvvarSetInt.argtypes = [c_kvEnvHandle, ctypes.c_int]
kvScriptEnvvarSetInt.restype = c_kvStatus
kvScriptEnvvarSetInt.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarGetInt = canlib32.kvScriptEnvvarGetInt
kvScriptEnvvarGetInt.argtypes = [c_kvEnvHandle, ctypes.c_void_p]
kvScriptEnvvarGetInt.restype = c_kvStatus
kvScriptEnvvarGetInt.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarSetData = canlib32.kvScriptEnvvarSetData
kvScriptEnvvarSetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarSetData.restype = c_kvStatus
kvScriptEnvvarSetData.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarGetData = canlib32.kvScriptEnvvarGetData
kvScriptEnvvarGetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarGetData.restype = c_kvStatus
kvScriptEnvvarGetData.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptGetMaxEnvvarSize = canlib32.kvScriptGetMaxEnvvarSize
kvScriptGetMaxEnvvarSize.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvScriptGetMaxEnvvarSize.restype = c_kvStatus
kvScriptGetMaxEnvvarSize.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptLoadFileOnDevice = canlib32.kvScriptLoadFileOnDevice
kvScriptLoadFileOnDevice.argtypes = [ctypes.c_int, ctypes.c_int,
                                     ctypes.c_char_p]
kvScriptLoadFileOnDevice.restype = c_kvStatus
kvScriptLoadFileOnDevice.errcheck = CANLIBErrorHandlers.CheckStatus

kvScriptLoadFile = canlib32.kvScriptLoadFile
kvScriptLoadFile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvScriptLoadFile.restype = c_kvStatus
kvScriptLoadFile.errcheck = CANLIBErrorHandlers.CheckStatus

kvFileCopyToDevice = canlib32.kvFileCopyToDevice
kvFileCopyToDevice.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvFileCopyToDevice.restype = c_kvStatus
kvFileCopyToDevice.errcheck = CANLIBErrorHandlers.CheckStatus

kvFileCopyFromDevice = canlib32.kvFileCopyFromDevice
kvFileCopyFromDevice.argtypes = [ctypes.c_int, ctypes.c_char_p,
                                 ctypes.c_char_p]
kvFileCopyFromDevice.restype = c_kvStatus
kvFileCopyFromDevice.errcheck = CANLIBErrorHandlers.CheckStatus

kvFileDelete = canlib32.kvFileDelete
kvFileDelete.argtypes = [ctypes.c_int, ctypes.c_char_p]
kvFileDelete.restype = c_kvStatus
kvFileDelete.errcheck = CANLIBErrorHandlers.CheckStatus

kvFileGetSystemData = canlib32.kvFileGetSystemData
kvFileGetSystemData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
kvFileGetSystemData.restype = c_kvStatus
kvFileGetSystemData.errcheck = CANLIBErrorHandlers.CheckStatus

import ctypes  #pragma: no cover
import sys  #pragma: no cover

#import canevt  #Kvaser have not implemented this yet
import CANLIBErrorHandlers
import canstat

if sys.platform == "win32":
    canlib32 = ctypes.WinDLL("canlib32")  #pragma: no cover
else:
    canlib32 = ctypes.CDLL("libcanlib.so")  #pragma: no cover

class c_canHandle(ctypes.c_int):
    pass

canINVALID_HANDLE = -1

canWANT_EXCLUSIVE = 0x0008
canWANT_EXTENDED = 0x0010
canWANT_VIRTUAL = 0x0020
canOPEN_EXCLUSIVE = canWANT_EXCLUSIVE
canOPEN_REQUIRE_EXTENDED = canWANT_EXTENDED
canOPEN_ACCEPT_VIRTUAL = canWANT_VIRTUAL
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200

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
canInitializeLibrary.restype = None
canInitializeLibrary.errCheck = None

canClose = canlib32.canClose
canClose.argtypes = [ctypes.c_int]
canClose.restype = canstat.c_canStatus
canClose.errCheck = CANLIBErrorHandlers.CheckStatus

canBusOn = canlib32.canBusOn
canBusOn.argtypes = [ctypes.c_int]
canBusOn.restype = canstat.c_canStatus
canBusOn.errCheck = CANLIBErrorHandlers.CheckStatus

canBusOff = canlib32.canBusOff
canBusOff.argtypes = [ctypes.c_int]
canBusOff.restype = canstat.c_canStatus
canBusOff.errCheck = CANLIBErrorHandlers.CheckStatus

canSetBusParams = canlib32.canSetBusParams
canSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                            ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
                            ctypes.c_uint]
canSetBusParams.resType = canstat.c_canStatus
canSetBusParams.errCheck = CANLIBErrorHandlers.CheckStatus

canGetBusParams = canlib32.canGetBusParams
canGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_void_p]
canGetBusParams.resType = canstat.c_canStatus
canGetBusParams.errCheck = CANLIBErrorHandlers.CheckStatus

canSetBusOutputControl = canlib32.canSetBusOutputControl
canSetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_uint]
canSetBusOutputControl.resType = canstat.c_canStatus
canSetBusOutputControl.errCheck = CANLIBErrorHandlers.CheckStatus

canGetBusOutputControl = canlib32.canGetBusOutputControl
canGetBusOutputControl.argtypes = [ctypes.c_int, ctypes.c_void_p]
canGetBusOutputControl.resType = canstat.c_canStatus
canGetBusOutputControl.errCheck = CANLIBErrorHandlers.CheckStatus

canAccept = canlib32.canAccept
canAccept.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint]
canAccept.resType = canstat.c_canStatus
canAccept.errCheck = CANLIBErrorHandlers.CheckStatus

canReadStatus = canlib32.canReadStatus
canReadStatus.argtypes = [ctypes.c_int, ctypes.c_void_p]
canReadStatus.resType = canstat.c_canStatus
canReadStatus.errCheck = CANLIBErrorHandlers.CheckStatus

canReadErrorCounters = canlib32.canReadErrorCounters
canReadErrorCounters.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canReadErrorCounters.resType = canstat.c_canStatus
canReadErrorCounters.errCheck = CANLIBErrorHandlers.CheckStatus

canWrite = canlib32.canWrite
canWrite.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                     ctypes.c_uint, ctypes.c_uint]
canWrite.resType = canstat.c_canStatus
canWrite.errCheck = CANLIBErrorHandlers.CheckStatus

canWriteSync = canlib32.canWriteSync
canWriteSync.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint]
canWriteSync.resType = canstat.c_canStatus
canWriteSync.errCheck = CANLIBErrorHandlers.CheckStatus

canRead = canlib32.canRead
canRead.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canRead.resType = canstat.c_canStatus
canRead.errCheck = CANLIBErrorHandlers.CheckStatusRead

canReadWait = canlib32.canReadWait
canReadWait.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                        ctypes.c_long]
canReadWait.resType = canstat.c_canStatus
canReadWait.errCheck = CANLIBErrorHandlers.CheckStatusRead

canReadSpecific = canlib32.canReadSpecific
canReadSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
canReadSpecific.resType = canstat.c_canStatus
canReadSpecific.errCheck = CANLIBErrorHandlers.CheckStatusRead

canReadSync = canlib32.canReadSync
canReadSync.argtypes = [ctypes.c_int, ctypes.c_ulong]
canReadSync.resType = canstat.c_canStatus
canReadSync.errCheck = CANLIBErrorHandlers.CheckStatusRead

canReadSyncSpecific = canlib32.canReadSyncSpecific
canReadSyncSpecific.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_ulong]
canReadSyncSpecific.resType = canstat.c_canStatus
canReadSyncSpecific.errCheck = CANLIBErrorHandlers.CheckStatusRead

canReadSpecificSkip = canlib32.canReadSpecificSkip
canReadSpecificSkip.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                                ctypes.c_void_p, ctypes.c_void_p,
                                ctypes.c_void_p]
canReadSpecificSkip.resType = canstat.c_canStatus
canReadSpecificSkip.errCheck = CANLIBErrorHandlers.CheckStatusRead

canSetNotify = canlib32.canSetNotify
canSetNotify.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_uint]
canSetNotify.resType = canstat.c_canStatus
canSetNotify.errCheck = CANLIBErrorHandlers.CheckStatus

canTranslateBaud = canlib32.canTranslateBaud
canTranslateBaud.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p,
                             ctypes.c_void_p, ctypes.c_void_p]
canTranslateBaud.resType = canstat.c_canStatus
canTranslateBaud.errCheck = CANLIBErrorHandlers.CheckStatus

canGetErrorText = canlib32.canGetErrorText
canGetErrorText.argtypes = [canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint]
canGetErrorText.resType = canstat.c_canStatus
canGetErrorText.errCheck = CANLIBErrorHandlers.CheckStatus

canGetVersion = canlib32.canGetVersion
canGetErrorText.argtypes = []
canGetErrorText.resType = ctypes.c_ushort
#canGetVersion doesn't return a canstat.c_canStatus value, so it has no error
#checking

canIoCtl = canlib32.canIoCtl
canIoCtl.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_void_p,
                     ctypes.c_uint]
canIoCtl.resType = canstat.c_canStatus
canIoCtl.errCheck = CANLIBErrorHandlers.CheckStatus

canReadTimer = canlib32.canReadTimer
canReadTimer.argtypes = [ctypes.c_int]
canReadTimer.resType = ctypes.c_ulong
#canReadTimer doesn't return a canstat.c_canStatus value, so it has no error
#checking

canOpenChannel = canlib32.canOpenChannel
canOpenChannel.argtypes = [ctypes.c_int, ctypes.c_int]
canOpenChannel.resType = ctypes.c_int
#canOpenChannel doesn't return a canstat.c_canStatus value, so it has no error
#checking

canGetNumberOfChannels = canlib32.canGetNumberOfChannels
canGetNumberOfChannels.argtypes = [ctypes.c_void_p]
canGetNumberOfChannels.resType = canstat.c_canStatus
canGetNumberOfChannels.errCheck = CANLIBErrorHandlers.CheckStatus

canGetChannelData = canlib32.canGetChannelData
canGetChannelData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                              ctypes.c_size_t]
canGetChannelData.resType = canstat.c_canStatus
canGetChannelData.errCheck = CANLIBErrorHandlers.CheckStatus

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
canWaitForEvent.resType = canstat.c_canStatus
canWaitForEvent.errCheck = CANLIBErrorHandlers.CheckStatus

canSetBusParamsC200 = canlib32.canSetBusParamsC200
canSetBusParamsC200.argtypes = [ctypes.c_int, ctypes.c_ubyte, ctypes.c_ubyte]
canSetBusParamsC200.resType = canstat.c_canStatus
canSetBusParamsC200.errCheck = CANLIBErrorHandlers.CheckStatus

canSetDriverMode = canlib32.canSetDriverMode
canSetDriverMode.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
canSetDriverMode.resType = canstat.c_canStatus
canSetDriverMode.errCheck = CANLIBErrorHandlers.CheckStatus

canGetDriverMode = canlib32.canGetDriverMode
canGetDriverMode.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
canGetDriverMode.resType = canstat.c_canStatus
canGetDriverMode.errCheck = CANLIBErrorHandlers.CheckStatus

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
canParamGetCount.resType = canstat.c_canStatus
canParamGetCount.errCheck = CANLIBErrorHandlers.CheckStatus

canParamCommitChanges = canlib32.canParamCommitChanges
canParamCommitChanges.argtypes = []
canParamCommitChanges.resType = canstat.c_canStatus
canParamCommitChanges.errCheck = CANLIBErrorHandlers.CheckStatus

canParamDeleteEntry = canlib32.canParamDeleteEntry
canParamDeleteEntry.argtypes = [ctypes.c_int]
canParamDeleteEntry.resType = canstat.c_canStatus
canParamDeleteEntry.errCheck = CANLIBErrorHandlers.CheckStatus

canParamCreateNewEntry = canlib32.canParamCreateNewEntry
canParamCreateNewEntry.argtypes = []
canParamCreateNewEntry.resType = canstat.c_canStatus
canParamCreateNewEntry.errCheck = CANLIBErrorHandlers.CheckStatus

canParamSwapEntries = canlib32.canParamSwapEntries
canParamSwapEntries.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSwapEntries.resType = canstat.c_canStatus
canParamSwapEntries.errCheck = CANLIBErrorHandlers.CheckStatus

canParamGetName = canlib32.canParamGetName
canParamGetName.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
canParamGetName.resType = canstat.c_canStatus
canParamGetName.errCheck = CANLIBErrorHandlers.CheckStatus


canParamGetChannelNumber = canlib32.canParamGetChannelNumber
canParamGetChannelNumber.argtypes = [ctypes.c_int]
canParamGetChannelNumber.resType = canstat.c_canStatus
canParamGetChannelNumber.errCheck = CANLIBErrorHandlers.CheckStatus

canParamGetBusParams = canlib32.canParamGetBusParams
canParamGetBusParams.argtypes = [ctypes.c_int, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p,
                                 ctypes.c_void_p, ctypes.c_void_p]
canParamGetBusParams.resType = canstat.c_canStatus
canParamGetBusParams.errCheck = CANLIBErrorHandlers.CheckStatus

canParamSetName = canlib32.canParamSetName
canParamSetName.argtypes = [ctypes.c_int, ctypes.c_char_p]
canParamSetName.resType = canstat.c_canStatus
canParamSetName.errCheck = CANLIBErrorHandlers.CheckStatus

canParamSetChannelNumber = canlib32.canParamSetChannelNumber
canParamSetChannelNumber.argtypes = [ctypes.c_int, ctypes.c_int]
canParamSetChannelNumber.resType = canstat.c_canStatus
canParamSetChannelNumber.errCheck = CANLIBErrorHandlers.CheckStatus

canParamSetBusParams = canlib32.canParamSetBusParams
canParamSetBusParams.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_uint,
                                 ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
canParamSetBusParams.resType = canstat.c_canStatus
canParamSetBusParams.errCheck = CANLIBErrorHandlers.CheckStatus

canParamFindByName = canlib32.canParamFindByName
canParamFindByName.argtypes = [ctypes.c_char_p]
canParamFindByName.resType = canstat.c_canStatus
canParamFindByName.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufFreeAll = canlib32.canObjBufFreeAll
canObjBufFreeAll.argtypes = [ctypes.c_int]
canObjBufFreeAll.resType = canstat.c_canStatus
canObjBufFreeAll.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufAllocate = canlib32.canObjBufAllocate
canObjBufAllocate.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufAllocate.resType = canstat.c_canStatus
canObjBufAllocate.errCheck = CANLIBErrorHandlers.CheckStatus

canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

canObjBufFree = canlib32.canObjBufFree
canObjBufFree.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufFree.resType = canstat.c_canStatus
canObjBufFree.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufWrite = canlib32.canObjBufWrite
canObjBufWrite.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
canObjBufWrite.resType = canstat.c_canStatus
canObjBufWrite.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetFilter = canlib32.canObjBufSetFilter
canObjBufSetFilter.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint,
                               ctypes.c_uint]
canObjBufSetFilter.resType = canstat.c_canStatus
canObjBufSetFilter.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetFlags = canlib32.canObjBufSetFlags
canObjBufSetFlags.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetFlags.resType = canstat.c_canStatus
canObjBufSetFlags.errCheck = CANLIBErrorHandlers.CheckStatus

canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

canObjBufSetPeriod = canlib32.canObjBufSetPeriod
canObjBufSetPeriod.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetPeriod.resType = canstat.c_canStatus
canObjBufSetPeriod.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufSetMsgCount = canlib32.canObjBufSetMsgCount
canObjBufSetMsgCount.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSetMsgCount.resType = canstat.c_canStatus
canObjBufSetMsgCount.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufEnable = canlib32.canObjBufEnable
canObjBufEnable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufEnable.resType = canstat.c_canStatus
canObjBufEnable.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufDisable = canlib32.canObjBufDisable
canObjBufDisable.argtypes = [ctypes.c_int, ctypes.c_int]
canObjBufDisable.resType = canstat.c_canStatus
canObjBufDisable.errCheck = CANLIBErrorHandlers.CheckStatus

canObjBufSendBurst = canlib32.canObjBufSendBurst
canObjBufSendBurst.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
canObjBufSendBurst.resType = canstat.c_canStatus
canObjBufSendBurst.errCheck = CANLIBErrorHandlers.CheckStatus

canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

canProbeVersion = canlib32.canProbeVersion
canProbeVersion.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                            ctypes.c_int, ctypes.c_uint]
canProbeVersion.resType = ctypes.c_bool
#canProbeVersion doesn't return a canstat.c_canStatus value, so it has no
#error checking

canResetBus = canlib32.canResetBus
canResetBus.argtypes = [ctypes.c_int]
canResetBus.resType = canstat.c_canStatus
canResetBus.errCheck = CANLIBErrorHandlers.CheckStatus

canWriteWait = canlib32.canWriteWait
canWriteWait.argtypes = [ctypes.c_int, ctypes.c_long, ctypes.c_void_p,
                         ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong]
canWriteWait.resType = canstat.c_canStatus
canWriteWait.errCheck = CANLIBErrorHandlers.CheckStatus

canUnloadLibrary = canlib32.canUnloadLibrary
canUnloadLibrary.argtypes = []
canUnloadLibrary.resType = canstat.c_canStatus
canUnloadLibrary.errCheck = CANLIBErrorHandlers.CheckStatus

canSetAcceptanceFilter = canlib32.canSetAcceptanceFilter
canSetAcceptanceFilter.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_uint,
                                   ctypes.c_int]
canSetAcceptanceFilter.resType = canstat.c_canStatus
canSetAcceptanceFilter.errCheck = CANLIBErrorHandlers.CheckStatus

canFlushReceiveQueue = canlib32.canFlushReceiveQueue
canFlushReceiveQueue.argtypes = [ctypes.c_int]
canFlushReceiveQueue.resType = canstat.c_canStatus
canFlushReceiveQueue.errCheck = CANLIBErrorHandlers.CheckStatus

canFlushTransmitQueue = canlib32.canFlushTransmitQueue
canFlushTransmitQueue.argtypes = [ctypes.c_int]
canFlushTransmitQueue.resType = canstat.c_canStatus
canFlushTransmitQueue.errCheck = CANLIBErrorHandlers.CheckStatus

kvGetApplicationMapping = canlib32.kvGetApplicationMapping
kvGetApplicationMapping.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                                    ctypes.c_void_p]
kvGetApplicationMapping.resType = canstat.c_canStatus
kvGetApplicationMapping.errCheck = CANLIBErrorHandlers.CheckStatus

kvBeep = canlib32.kvBeep
kvBeep.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_uint]
kvBeep.resType = canstat.c_canStatus
kvBeep.errCheck = CANLIBErrorHandlers.CheckStatus

kvSelfTest = canlib32.kvSelfTest
kvSelfTest.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvSelfTest.resType = canstat.c_canStatus
kvSelfTest.errCheck = CANLIBErrorHandlers.CheckStatus

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
kvFlashLeds.resType = canstat.c_canStatus
kvFlashLeds.errCheck = CANLIBErrorHandlers.CheckStatus

canRequestChipStatus = canlib32.canRequestChipStatus
canRequestChipStatus.argtypes = [ctypes.c_int]
canRequestChipStatus.resType = canstat.c_canStatus
canRequestChipStatus.errCheck = CANLIBErrorHandlers.CheckStatus

canRequestBusStatistics = canlib32.canRequestBusStatistics
canRequestBusStatistics.argtypes = [ctypes.c_int]
canRequestBusStatistics.resType = canstat.c_canStatus
canRequestBusStatistics.errCheck = CANLIBErrorHandlers.CheckStatus


class c_canBusStatistics(ctypes.Structure):
    _fields_ = [("stdData", ctypes.c_ulong), ("stdRemote", ctypes.c_ulong),
      ("extData", ctypes.c_ulong), ("extRemote", ctypes.c_ulong),
      ("errFrame", ctypes.c_ulong), ("busLoad", ctypes.c_ulong),
      ("overruns", ctypes.c_ulong)]

canGetBusStatistics = canlib32.canGetBusStatistics
canGetBusStatistics.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
canGetBusStatistics.resType = canstat.c_canStatus
canGetBusStatistics.errCheck = CANLIBErrorHandlers.CheckStatus

canSetBitrate = canlib32.canSetBitrate
canSetBitrate.argtypes = [ctypes.c_int, ctypes.c_int]
canSetBitrate.resType = canstat.c_canStatus
canSetBitrate.errCheck = CANLIBErrorHandlers.CheckStatus

kvAnnounceIdentity = canlib32.kvAnnounceIdentity
kvAnnounceIdentity.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t]
kvAnnounceIdentity.resType = canstat.c_canStatus
kvAnnounceIdentity.errCheck = CANLIBErrorHandlers.CheckStatus

canGetHandleData = canlib32.canGetHandleData
canGetHandleData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p,
                             ctypes.c_size_t]
canGetHandleData.resType = canstat.c_canStatus
canGetHandleData.errCheck = CANLIBErrorHandlers.CheckStatus


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
kvTimeDomainCreate.resType = c_kvStatus
kvTimeDomainCreate.errCheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainDelete = canlib32.kvTimeDomainDelete
kvTimeDomainDelete.argtypes = [c_kvTimeDomain]
kvTimeDomainDelete.resType = c_kvStatus
kvTimeDomainDelete.errCheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainResetTime = canlib32.kvTimeDomainResetTime
kvTimeDomainResetTime.argtypes = [c_kvTimeDomain]
kvTimeDomainResetTime.resType = c_kvStatus
kvTimeDomainResetTime.errCheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainGetData = canlib32.kvTimeDomainGetData
kvTimeDomainGetData.argtypes = [c_kvTimeDomain, ctypes.c_void_p, ctypes.c_size_t]
kvTimeDomainGetData.resType = c_kvStatus
kvTimeDomainGetData.errCheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainAddHandle = canlib32.kvTimeDomainAddHandle
kvTimeDomainAddHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainAddHandle.resType = c_kvStatus
kvTimeDomainAddHandle.errCheck = CANLIBErrorHandlers.CheckStatus

kvTimeDomainRemoveHandle = canlib32.kvTimeDomainRemoveHandle
kvTimeDomainRemoveHandle.argtypes = [c_kvTimeDomain, ctypes.c_int]
kvTimeDomainRemoveHandle.resType = c_kvStatus
kvTimeDomainRemoveHandle.errCheck = CANLIBErrorHandlers.CheckStatus


class c_kvCallback(ctypes.c_void_p):
    pass

CALLBACKFUNC = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
NULL_CALLBACK = ctypes.cast(None, CALLBACKFUNC)

kvSetNotifyCallback = canlib32.kvSetNotifyCallback
kvSetNotifyCallback.argtypes = [ctypes.c_int, c_kvCallback, ctypes.c_void_p,
                                ctypes.c_uint]
kvSetNotifyCallback.resType = c_kvStatus
kvSetNotifyCallback.errCheck = CANLIBErrorHandlers.CheckStatus

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
kvGetSupportedInterfaceInfo.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
  ctypes.c_void_p, ctypes.c_void_p]
kvGetSupportedInterfaceInfo.resType = c_kvStatus
kvGetSupportedInterfaceInfo.errCheck = CANLIBErrorHandlers.CheckStatus

kvReadTimer = canlib32.kvReadTimer
kvReadTimer.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer.resType = c_kvStatus
kvReadTimer.errCheck = CANLIBErrorHandlers.CheckStatus

kvReadTimer64 = canlib32.kvReadTimer64
kvReadTimer64.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvReadTimer64.resType = c_kvStatus
kvReadTimer64.errCheck = CANLIBErrorHandlers.CheckStatus

kvReadDeviceCustomerData = canlib32.kvReadDeviceCustomerData
kvReadDeviceCustomerData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                     ctypes.c_void_p, ctypes.c_size_t]
kvReadDeviceCustomerData.resType = c_kvStatus
kvReadDeviceCustomerData.errCheck = CANLIBErrorHandlers.CheckStatus

ENVVAR_TYPE_INT = 1
ENVVAR_TYPE_FLOAT = 2
ENVVAR_TYPE_STRING = 3


class c_kvEnvHandle(ctypes.c_longlong):
    pass

kvScriptStart = canlib32.kvScriptStart
kvScriptStart.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStart.resType = c_kvStatus
kvScriptStart.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptStop = canlib32.kvScriptStop
kvScriptStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptStop.resType = c_kvStatus
kvScriptStop.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptForceStop = canlib32.kvScriptForceStop
kvScriptForceStop.argtypes = [ctypes.c_int, ctypes.c_int]
kvScriptForceStop.resType = c_kvStatus
kvScriptForceStop.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptSendEvent = canlib32.kvScriptSendEvent
kvScriptSendEvent.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                              ctypes.c_int]
kvScriptSendEvent.resType = c_kvStatus
kvScriptSendEvent.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarOpen = canlib32.kvScriptEnvvarOpen
kvScriptEnvvarOpen.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                               ctypes.c_void_p, ctypes.c_void_p]
kvScriptEnvvarOpen.resType = c_kvEnvHandle
#Since kvScriptEnvvarOpen doesn't return a status value, it has no error
#checking

kvScriptEnvvarClose = canlib32.kvScriptEnvvarClose
kvScriptEnvvarClose.argtypes = [c_kvEnvHandle]
kvScriptEnvvarClose.resType = c_kvStatus
kvScriptEnvvarClose.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarSetInt = canlib32.kvScriptEnvvarSetInt
kvScriptEnvvarSetInt.argtypes = [c_kvEnvHandle, ctypes.c_int]
kvScriptEnvvarSetInt.resType = c_kvStatus
kvScriptEnvvarSetInt.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarGetInt = canlib32.kvScriptEnvvarGetInt
kvScriptEnvvarGetInt.argtypes = [c_kvEnvHandle, ctypes.c_void_p]
kvScriptEnvvarGetInt.resType = c_kvStatus
kvScriptEnvvarGetInt.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarSetData = canlib32.kvScriptEnvvarSetData
kvScriptEnvvarSetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarSetData.resType = c_kvStatus
kvScriptEnvvarSetData.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptEnvvarGetData = canlib32.kvScriptEnvvarGetData
kvScriptEnvvarGetData.argtypes = [c_kvEnvHandle, ctypes.c_void_p,
                                  ctypes.c_int, ctypes.c_int]
kvScriptEnvvarGetData.resType = c_kvStatus
kvScriptEnvvarGetData.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptGetMaxEnvvarSize = canlib32.kvScriptGetMaxEnvvarSize
kvScriptGetMaxEnvvarSize.argtypes = [ctypes.c_int, ctypes.c_void_p]
kvScriptGetMaxEnvvarSize.resType = c_kvStatus
kvScriptGetMaxEnvvarSize.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptLoadFileOnDevice = canlib32.kvScriptLoadFileOnDevice
kvScriptLoadFileOnDevice.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvScriptLoadFileOnDevice.resType = c_kvStatus
kvScriptLoadFileOnDevice.errCheck = CANLIBErrorHandlers.CheckStatus

kvScriptLoadFile = canlib32.kvScriptLoadFile
kvScriptLoadFile.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvScriptLoadFile.resType = c_kvStatus
kvScriptLoadFile.errCheck = CANLIBErrorHandlers.CheckStatus

kvFileCopyToDevice = canlib32.kvFileCopyToDevice
kvFileCopyToDevice.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_char_p]
kvFileCopyToDevice.resType = c_kvStatus
kvFileCopyToDevice.errCheck = CANLIBErrorHandlers.CheckStatus

kvFileCopyFromDevice = canlib32.kvFileCopyFromDevice
kvFileCopyFromDevice.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p]
kvFileCopyFromDevice.resType = c_kvStatus
kvFileCopyFromDevice.errCheck = CANLIBErrorHandlers.CheckStatus

kvFileDelete = canlib32.kvFileDelete
kvFileDelete.argtypes = [ctypes.c_int, ctypes.c_char_p]
kvFileDelete.resType = c_kvStatus
kvFileDelete.errCheck = CANLIBErrorHandlers.CheckStatus

kvFileGetSystemData = canlib32.kvFileGetSystemData
kvFileGetSystemData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
kvFileGetSystemData.resType = c_kvStatus
kvFileGetSystemData.errCheck = CANLIBErrorHandlers.CheckStatus

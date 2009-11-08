from ctypes import *
import sys
sys.path.append("..")
from canstat import *
#from canevt import *#Kvaser have not implemented this yet
from CANLIBErrorHandlers import *

if sys.platform == "win32":
    canlib32 = WinDLL("canlib32")
else:
    canlib32 = CDLL("libcanlib.so")


class c_canHandle(c_int):
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
canClose.argtypes = [c_int]
canClose.restype = c_canStatus
canClose.errCheck = CheckStatus

canBusOn = canlib32.canBusOn
canBusOn.argtypes = [c_int]
canBusOn.restype = c_canStatus
canBusOn.errCheck = CheckStatus

canBusOff = canlib32.canBusOff
canBusOff.argtypes = [c_int]
canBusOff.restype = c_canStatus
canBusOff.errCheck = CheckStatus

canSetBusParams = canlib32.canSetBusParams
canSetBusParams.argtypes = [c_int, c_long, c_uint, c_uint, c_uint, c_uint,
  c_uint]
canSetBusParams.resType = c_canStatus
canSetBusParams.errCheck = CheckStatus

canGetBusParams = canlib32.canGetBusParams
canGetBusParams.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p, c_void_p]
canGetBusParams.resType = c_canStatus
canGetBusParams.errCheck = CheckStatus

canSetBusOutputControl = canlib32.canSetBusOutputControl
canSetBusOutputControl.argtypes = [c_int, c_uint]
canSetBusOutputControl.resType = c_canStatus
canSetBusOutputControl.errCheck = CheckStatus

canGetBusOutputControl = canlib32.canGetBusOutputControl
canGetBusOutputControl.argtypes = [c_int, c_void_p]
canGetBusOutputControl.resType = c_canStatus
canGetBusOutputControl.errCheck = CheckStatus

canAccept = canlib32.canAccept
canAccept.argtypes = [c_int, c_long, c_uint]
canAccept.resType = c_canStatus
canAccept.errCheck = CheckStatus

canReadStatus = canlib32.canReadStatus
canReadStatus.argtypes = [c_int, c_void_p]
canReadStatus.resType = c_canStatus
canReadStatus.errCheck = CheckStatus

canReadErrorCounters = canlib32.canReadErrorCounters
canReadErrorCounters.argtypes = [c_int, c_void_p, c_void_p, c_void_p]
canReadErrorCounters.resType = c_canStatus
canReadErrorCounters.errCheck = CheckStatus

canWrite = canlib32.canWrite
canWrite.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint]
canWrite.resType = c_canStatus
canWrite.errCheck = CheckStatus

canWriteSync = canlib32.canWriteSync
canWriteSync.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint]
canWriteSync.resType = c_canStatus
canWriteSync.errCheck = CheckStatus

canRead = canlib32.canRead
canRead.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p, c_void_p]
canRead.resType = c_canStatus
canRead.errCheck = CheckStatusRead

canReadWait = canlib32.canReadWait
canReadWait.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p, c_long]
canReadWait.resType = c_canStatus
canReadWait.errCheck = CheckStatusRead

canReadSpecific = canlib32.canReadSpecific
canReadSpecific.argtypes = [c_int, c_long, c_void_p, c_void_p, c_void_p,
  c_void_p]
canReadSpecific.resType = c_canStatus
canReadSpecific.errCheck = CheckStatusRead

canReadSync = canlib32.canReadSync
canReadSync.argtypes = [c_int, c_ulong]
canReadSync.resType = c_canStatus
canReadSync.errCheck = CheckStatusRead

canReadSyncSpecific = canlib32.canReadSyncSpecific
canReadSyncSpecific.argtypes = [c_int, c_long, c_ulong]
canReadSyncSpecific.resType = c_canStatus
canReadSyncSpecific.errCheck = CheckStatusRead

canReadSpecificSkip = canlib32.canReadSpecificSkip
canReadSpecificSkip.argtypes = [c_int, c_long, c_void_p, c_void_p, c_void_p,
  c_void_p]
canReadSpecificSkip.resType = c_canStatus
canReadSpecificSkip.errCheck = CheckStatusRead

canSetNotify = canlib32.canSetNotify
canSetNotify.argtypes = [c_int, c_void_p, c_uint]
canSetNotify.resType = c_canStatus
canSetNotify.errCheck = CheckStatus

canTranslateBaud = canlib32.canTranslateBaud
canTranslateBaud.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p]
canTranslateBaud.resType = c_canStatus
canTranslateBaud.errCheck = CheckStatus

canGetErrorText = canlib32.canGetErrorText
canGetErrorText.argtypes = [c_canStatus, c_char_p, c_uint]
canGetErrorText.resType = c_canStatus
canGetErrorText.errCheck = CheckStatus

canGetVersion = canlib32.canGetVersion
canGetErrorText.argtypes = []
canGetErrorText.resType = c_ushort
#canGetVersion doesn't return a c_canStatus value, so it has no error checking

canIoCtl = canlib32.canIoCtl
canIoCtl.argtypes = [c_int, c_uint, c_void_p, c_uint]
canIoCtl.resType = c_canStatus
canIoCtl.errCheck = CheckStatus

canReadTimer = canlib32.canReadTimer
canReadTimer.argtypes = [c_int]
canReadTimer.resType = c_ulong
#canReadTimer doesn't return a c_canStatus value, so it has no error checking

canOpenChannel = canlib32.canOpenChannel
canOpenChannel.argtypes = [c_int, c_int]
canOpenChannel.resType = c_int
#canOpenChannel doesn't return a c_canStatus value, so it has no error checking

canGetNumberOfChannels = canlib32.canGetNumberOfChannels
canGetNumberOfChannels.argtypes = [c_void_p]
canGetNumberOfChannels.resType = c_canStatus
canGetNumberOfChannels.errCheck = CheckStatus

canGetChannelData = canlib32.canGetChannelData
#TO-DO: is size_t actually a c_int or is it something else?
canGetChannelData.argtypes = [c_int, c_int, c_void_p, c_int]
canGetChannelData.resType = c_canStatus
canGetChannelData.errCheck = CheckStatus

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


class c_canUserIOPortData(Structure):
    _fields_ = [("portNo", c_uint), ("portValue", c_uint)]

canWaitForEvent = canlib32.canWaitForEvent
canWaitForEvent.argtypes = [c_int, c_ulong]
canWaitForEvent.resType = c_canStatus
canWaitForEvent.errCheck = CheckStatus

canSetBusParamsC200 = canlib32.canSetBusParamsC200
canSetBusParamsC200.argtypes = [c_int, c_ubyte, c_ubyte]
canSetBusParamsC200.resType = c_canStatus
canSetBusParamsC200.errCheck = CheckStatus

canSetDriverMode = canlib32.canSetDriverMode
canSetDriverMode.argtypes = [c_int, c_int, c_int]
canSetDriverMode.resType = c_canStatus
canSetDriverMode.errCheck = CheckStatus

canGetDriverMode = canlib32.canGetDriverMode
canGetDriverMode.argtypes = [c_int, c_void_p, c_void_p]
canGetDriverMode.resType = c_canStatus
canGetDriverMode.errCheck = CheckStatus

canVERSION_CANLIB32_VERSION = 0
canVERSION_CANLIB32_PRODVER = 1
canVERSION_CANLIB32_PRODVER32 = 2
canVERSION_CANLIB32_BETA = 3

canGetVersionEx = canlib32.canGetVersionEx
canGetVersionEx.argtypes = [c_uint]
canGetVersionEx.restype = c_uint
#canGetVersionEx doesn't return a c_canStatus value, so it has no error
#checking

canParamGetCount = canlib32.canParamGetCount
canParamGetCount.argtypes = []
canParamGetCount.resType = c_canStatus
canParamGetCount.errCheck = CheckStatus

canParamCommitChanges = canlib32.canParamCommitChanges
canParamCommitChanges.argtypes = []
canParamCommitChanges.resType = c_canStatus
canParamCommitChanges.errCheck = CheckStatus

canParamDeleteEntry = canlib32.canParamDeleteEntry
canParamDeleteEntry.argtypes = [c_int]
canParamDeleteEntry.resType = c_canStatus
canParamDeleteEntry.errCheck = CheckStatus

canParamCreateNewEntry = canlib32.canParamCreateNewEntry
canParamCreateNewEntry.argtypes = []
canParamCreateNewEntry.resType = c_canStatus
canParamCreateNewEntry.errCheck = CheckStatus

canParamSwapEntries = canlib32.canParamSwapEntries
canParamSwapEntries.argtypes = [c_int, c_int]
canParamSwapEntries.resType = c_canStatus
canParamSwapEntries.errCheck = CheckStatus

canParamGetName = canlib32.canParamGetName
canParamGetName.argtypes = [c_int, c_char_p, c_int]
canParamGetName.resType = c_canStatus
canParamGetName.errCheck = CheckStatus


canParamGetChannelNumber = canlib32.canParamGetChannelNumber
canParamGetChannelNumber.argtypes = [c_int]
canParamGetChannelNumber.resType = c_canStatus
canParamGetChannelNumber.errCheck = CheckStatus

canParamGetBusParams = canlib32.canParamGetBusParams
canParamGetBusParams.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p]
canParamGetBusParams.resType = c_canStatus
canParamGetBusParams.errCheck = CheckStatus

canParamSetName = canlib32.canParamSetName
canParamSetName.argtypes = [c_int, c_char_p]
canParamSetName.resType = c_canStatus
canParamSetName.errCheck = CheckStatus

canParamSetChannelNumber = canlib32.canParamSetChannelNumber
canParamSetChannelNumber.argtypes = [c_int, c_int]
canParamSetChannelNumber.resType = c_canStatus
canParamSetChannelNumber.errCheck = CheckStatus

canParamSetBusParams = canlib32.canParamSetBusParams
canParamSetBusParams.argtypes = [c_int, c_long, c_uint, c_uint, c_uint, c_uint]
canParamSetBusParams.resType = c_canStatus
canParamSetBusParams.errCheck = CheckStatus

canParamFindByName = canlib32.canParamFindByName
canParamFindByName.argtypes = [c_char_p]
canParamFindByName.resType = c_canStatus
canParamFindByName.errCheck = CheckStatus

canObjBufFreeAll = canlib32.canObjBufFreeAll
canObjBufFreeAll.argtypes = [c_int]
canObjBufFreeAll.resType = c_canStatus
canObjBufFreeAll.errCheck = CheckStatus

canObjBufAllocate = canlib32.canObjBufAllocate
canObjBufAllocate.argtypes = [c_int, c_int]
canObjBufAllocate.resType = c_canStatus
canObjBufAllocate.errCheck = CheckStatus

canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

canObjBufFree = canlib32.canObjBufFree
canObjBufFree.argtypes = [c_int, c_int]
canObjBufFree.resType = c_canStatus
canObjBufFree.errCheck = CheckStatus

canObjBufWrite = canlib32.canObjBufWrite
canObjBufWrite.argtypes = [c_int, c_int, c_int, c_void_p, c_uint, c_uint]
canObjBufWrite.resType = c_canStatus
canObjBufWrite.errCheck = CheckStatus

canObjBufSetFilter = canlib32.canObjBufSetFilter
canObjBufSetFilter.argtypes = [c_int, c_int, c_uint, c_uint]
canObjBufSetFilter.resType = c_canStatus
canObjBufSetFilter.errCheck = CheckStatus

canObjBufSetFlags = canlib32.canObjBufSetFlags
canObjBufSetFlags.argtypes = [c_int, c_int, c_uint]
canObjBufSetFlags.resType = c_canStatus
canObjBufSetFlags.errCheck = CheckStatus

canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

canObjBufSetPeriod = canlib32.canObjBufSetPeriod
canObjBufSetPeriod.argtypes = [c_int, c_int, c_uint]
canObjBufSetPeriod.resType = c_canStatus
canObjBufSetPeriod.errCheck = CheckStatus

canObjBufSetMsgCount = canlib32.canObjBufSetMsgCount
canObjBufSetMsgCount.argtypes = [c_int, c_int, c_uint]
canObjBufSetMsgCount.resType = c_canStatus
canObjBufSetMsgCount.errCheck = CheckStatus

canObjBufEnable = canlib32.canObjBufEnable
canObjBufEnable.argtypes = [c_int, c_int]
canObjBufEnable.resType = c_canStatus
canObjBufEnable.errCheck = CheckStatus

canObjBufDisable = canlib32.canObjBufDisable
canObjBufDisable.argtypes = [c_int, c_int]
canObjBufDisable.resType = c_canStatus
canObjBufDisable.errCheck = CheckStatus

canObjBufSendBurst = canlib32.canObjBufSendBurst
canObjBufSendBurst.argtypes = [c_int, c_int, c_uint]
canObjBufSendBurst.resType = c_canStatus
canObjBufSendBurst.errCheck = CheckStatus

canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

canProbeVersion = canlib32.canProbeVersion
canProbeVersion.argtypes = [c_int, c_int, c_int, c_int, c_uint]
canProbeVersion.resType = c_bool
#canProbeVersion doesn't return a c_canStatus value, so it has no error
#checking

canResetBus = canlib32.canResetBus
canResetBus.argtypes = [c_int]
canResetBus.resType = c_canStatus
canResetBus.errCheck = CheckStatus

canWriteWait = canlib32.canWriteWait
canWriteWait.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint, c_ulong]
canWriteWait.resType = c_canStatus
canWriteWait.errCheck = CheckStatus

canUnloadLibrary = canlib32.canUnloadLibrary
canUnloadLibrary.argtypes = []
canUnloadLibrary.resType = c_canStatus
canUnloadLibrary.errCheck = CheckStatus

canSetAcceptanceFilter = canlib32.canSetAcceptanceFilter
canSetAcceptanceFilter.argtypes = [c_int, c_uint, c_uint, c_int]
canSetAcceptanceFilter.resType = c_canStatus
canSetAcceptanceFilter.errCheck = CheckStatus

canFlushReceiveQueue = canlib32.canFlushReceiveQueue
canFlushReceiveQueue.argtypes = [c_int]
canFlushReceiveQueue.resType = c_canStatus
canFlushReceiveQueue.errCheck = CheckStatus

canFlushTransmitQueue = canlib32.canFlushTransmitQueue
canFlushTransmitQueue.argtypes = [c_int]
canFlushTransmitQueue.resType = c_canStatus
canFlushTransmitQueue.errCheck = CheckStatus

kvGetApplicationMapping = canlib32.kvGetApplicationMapping
kvGetApplicationMapping.argtypes = [c_int, c_char_p, c_int, c_void_p]
kvGetApplicationMapping.resType = c_canStatus
kvGetApplicationMapping.errCheck = CheckStatus

kvBeep = canlib32.kvBeep
kvBeep.argtypes = [c_int, c_int, c_uint]
kvBeep.resType = c_canStatus
kvBeep.errCheck = CheckStatus

kvSelfTest = canlib32.kvSelfTest
kvSelfTest.argtypes = [c_int, c_void_p]
kvSelfTest.resType = c_canStatus
kvSelfTest.errCheck = CheckStatus

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
kvFlashLeds.argtypes = [c_int, c_int, c_int]
kvFlashLeds.resType = c_canStatus
kvFlashLeds.errCheck = CheckStatus

canRequestChipStatus = canlib32.canRequestChipStatus
canRequestChipStatus.argtypes = [c_int]
canRequestChipStatus.resType = c_canStatus
canRequestChipStatus.errCheck = CheckStatus

canRequestBusStatistics = canlib32.canRequestBusStatistics
canRequestBusStatistics.argtypes = [c_int]
canRequestBusStatistics.resType = c_canStatus
canRequestBusStatistics.errCheck = CheckStatus


class c_canBusStatistics(Structure):
    _fields_ = [("stdData", c_ulong), ("stdRemote", c_ulong),
      ("extData", c_ulong), ("extRemote", c_ulong), ("errFrame", c_ulong),
      ("busLoad", c_ulong), ("overruns", c_ulong)]

canGetBusStatistics = canlib32.canGetBusStatistics
#TO-DO: is size_t a c_int?
canGetBusStatistics.argtypes = [c_int, c_void_p, c_int]
canGetBusStatistics.resType = c_canStatus
canGetBusStatistics.errCheck = CheckStatus

canSetBitrate = canlib32.canSetBitrate
canSetBitrate.argtypes = [c_int, c_int]
canSetBitrate.resType = c_canStatus
canSetBitrate.errCheck = CheckStatus

kvAnnounceIdentity = canlib32.kvAnnounceIdentity
#TO-DO: is size_t a c_int?
kvAnnounceIdentity.argtypes = [c_int, c_void_p, c_int]
kvAnnounceIdentity.resType = c_canStatus
kvAnnounceIdentity.errCheck = CheckStatus

canGetHandleData = canlib32.canGetHandleData
#TO-DO: is size_t a c_int?
canGetHandleData.argtypes = [c_int, c_int, c_void_p, c_int]
canGetHandleData.resType = c_canStatus
canGetHandleData.errCheck = CheckStatus


class c_kvTimeDomain(c_void_p):
    pass


class c_kvStatus(c_canStatus):
    pass


class c_kvTimeDomainData(Structure):
    _fields_ = [("nMagiSyncGroups", c_int), ("nMagiSyncedMembers", c_int),
      ("nNonMagiSyncCards", c_int), ("nNonMagiSyncedMembers", c_int)]

kvTimeDomainCreate = canlib32.kvTimeDomainCreate
kvTimeDomainCreate.argtypes = [c_kvTimeDomain]
kvTimeDomainCreate.resType = c_kvStatus
kvTimeDomainCreate.errCheck = CheckStatus

kvTimeDomainDelete = canlib32.kvTimeDomainDelete
kvTimeDomainDelete.argtypes = [c_kvTimeDomain]
kvTimeDomainDelete.resType = c_kvStatus
kvTimeDomainDelete.errCheck = CheckStatus

kvTimeDomainResetTime = canlib32.kvTimeDomainResetTime
kvTimeDomainResetTime.argtypes = [c_kvTimeDomain]
kvTimeDomainResetTime.resType = c_kvStatus
kvTimeDomainResetTime.errCheck = CheckStatus

kvTimeDomainGetData = canlib32.kvTimeDomainGetData
#TO-DO: is size_t a c_int?
kvTimeDomainGetData.argtypes = [c_kvTimeDomain, c_void_p, c_int]
kvTimeDomainGetData.resType = c_kvStatus
kvTimeDomainGetData.errCheck = CheckStatus

kvTimeDomainAddHandle = canlib32.kvTimeDomainAddHandle
kvTimeDomainAddHandle.argtypes = [c_kvTimeDomain, c_int]
kvTimeDomainAddHandle.resType = c_kvStatus
kvTimeDomainAddHandle.errCheck = CheckStatus

kvTimeDomainRemoveHandle = canlib32.kvTimeDomainRemoveHandle
kvTimeDomainRemoveHandle.argtypes = [c_kvTimeDomain, c_int]
kvTimeDomainRemoveHandle.resType = c_kvStatus
kvTimeDomainRemoveHandle.errCheck = CheckStatus


class c_kvCallback(c_void_p):
    pass

CALLBACKFUNC = CFUNCTYPE(c_int, c_int)
NULL_CALLBACK = cast(None, CALLBACKFUNC)

kvSetNotifyCallback = canlib32.kvSetNotifyCallback
kvSetNotifyCallback.argtypes = [c_int, c_kvCallback, c_void_p, c_uint]
kvSetNotifyCallback.resType = c_kvStatus
kvSetNotifyCallback.errCheck = CheckStatus

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
kvGetSupportedInterfaceInfo.argtypes = [c_int, c_char_p, c_int, c_void_p,
  c_void_p]
kvGetSupportedInterfaceInfo.resType = c_kvStatus
kvGetSupportedInterfaceInfo.errCheck = CheckStatus

kvReadTimer = canlib32.kvReadTimer
kvReadTimer.argtypes = [c_int, c_void_p]
kvReadTimer.resType = c_kvStatus
kvReadTimer.errCheck = CheckStatus

kvReadTimer64 = canlib32.kvReadTimer64
kvReadTimer64.argtypes = [c_int, c_void_p]
kvReadTimer64.resType = c_kvStatus
kvReadTimer64.errCheck = CheckStatus

kvReadDeviceCustomerData = canlib32.kvReadDeviceCustomerData
#TO-DO: is size_t a c_int?
kvReadDeviceCustomerData.argtypes = [c_int, c_int, c_int, c_void_p, c_int]
kvReadDeviceCustomerData.resType = c_kvStatus
kvReadDeviceCustomerData.errCheck = CheckStatus

ENVVAR_TYPE_INT = 1
ENVVAR_TYPE_FLOAT = 2
ENVVAR_TYPE_STRING = 3


class c_kvEnvHandle(c_longlong):
    pass

kvScriptStart = canlib32.kvScriptStart
kvScriptStart.argtypes = [c_int, c_int]
kvScriptStart.resType = c_kvStatus
kvScriptStart.errCheck = CheckStatus

kvScriptStop = canlib32.kvScriptStop
kvScriptStop.argtypes = [c_int, c_int]
kvScriptStop.resType = c_kvStatus
kvScriptStop.errCheck = CheckStatus

kvScriptForceStop = canlib32.kvScriptForceStop
kvScriptForceStop.argtypes = [c_int, c_int]
kvScriptForceStop.resType = c_kvStatus
kvScriptForceStop.errCheck = CheckStatus

kvScriptSendEvent = canlib32.kvScriptSendEvent
kvScriptSendEvent.argtypes = [c_int, c_int, c_int, c_int]
kvScriptSendEvent.resType = c_kvStatus
kvScriptSendEvent.errCheck = CheckStatus

kvScriptEnvvarOpen = canlib32.kvScriptEnvvarOpen
kvScriptEnvvarOpen.argtypes = [c_int, c_char_p, c_int, c_void_p, c_void_p]
kvScriptEnvvarOpen.resType = c_kvEnvHandle
#Since kvScriptEnvvarOpen doesn't return a status value, it has no error
#checking

kvScriptEnvvarClose = canlib32.kvScriptEnvvarClose
kvScriptEnvvarClose.argtypes = [c_kvEnvHandle]
kvScriptEnvvarClose.resType = c_kvStatus
kvScriptEnvvarClose.errCheck = CheckStatus

kvScriptEnvvarSetInt = canlib32.kvScriptEnvvarSetInt
kvScriptEnvvarSetInt.argtypes = [c_kvEnvHandle, c_int]
kvScriptEnvvarSetInt.resType = c_kvStatus
kvScriptEnvvarSetInt.errCheck = CheckStatus

kvScriptEnvvarGetInt = canlib32.kvScriptEnvvarGetInt
kvScriptEnvvarGetInt.argtypes = [c_kvEnvHandle, c_void_p]
kvScriptEnvvarGetInt.resType = c_kvStatus
kvScriptEnvvarGetInt.errCheck = CheckStatus

kvScriptEnvvarSetData = canlib32.kvScriptEnvvarSetData
kvScriptEnvvarSetData.argtypes = [c_kvEnvHandle, c_void_p, c_int, c_int]
kvScriptEnvvarSetData.resType = c_kvStatus
kvScriptEnvvarSetData.errCheck = CheckStatus

kvScriptEnvvarGetData = canlib32.kvScriptEnvvarGetData
kvScriptEnvvarGetData.argtypes = [c_kvEnvHandle, c_void_p, c_int, c_int]
kvScriptEnvvarGetData.resType = c_kvStatus
kvScriptEnvvarGetData.errCheck = CheckStatus

kvScriptGetMaxEnvvarSize = canlib32.kvScriptGetMaxEnvvarSize
kvScriptGetMaxEnvvarSize.argtypes = [c_int, c_void_p]
kvScriptGetMaxEnvvarSize.resType = c_kvStatus
kvScriptGetMaxEnvvarSize.errCheck = CheckStatus

kvScriptLoadFileOnDevice = canlib32.kvScriptLoadFileOnDevice
kvScriptLoadFileOnDevice.argtypes = [c_int, c_int, c_char_p]
kvScriptLoadFileOnDevice.resType = c_kvStatus
kvScriptLoadFileOnDevice.errCheck = CheckStatus

kvScriptLoadFile = canlib32.kvScriptLoadFile
kvScriptLoadFile.argtypes = [c_int, c_int, c_char_p]
kvScriptLoadFile.resType = c_kvStatus
kvScriptLoadFile.errCheck = CheckStatus

kvFileCopyToDevice = canlib32.kvFileCopyToDevice
kvFileCopyToDevice.argtypes = [c_int, c_int, c_char_p]
kvFileCopyToDevice.resType = c_kvStatus
kvFileCopyToDevice.errCheck = CheckStatus

kvFileCopyFromDevice = canlib32.kvFileCopyFromDevice
kvFileCopyFromDevice.argtypes = [c_int, c_char_p, c_char_p]
kvFileCopyFromDevice.resType = c_kvStatus
kvFileCopyFromDevice.errCheck = CheckStatus

kvFileDelete = canlib32.kvFileDelete
kvFileDelete.argtypes = [c_int, c_char_p]
kvFileDelete.resType = c_kvStatus
kvFileDelete.errCheck = CheckStatus

kvFileGetSystemData = canlib32.kvFileGetSystemData
kvFileGetSystemData.argtypes = [c_int, c_int, c_void_p]
kvFileGetSystemData.resType = c_kvStatus
kvFileGetSystemData.errCheck = CheckStatus


"""
                   Copyright 1994-2008 by KVASER AB, SWEDEN      
                        WWW: http://www.kvaser.com

 This software is furnished under a license and may be used and copied
 only in accordance with the terms of such license.

 Description:
   Definitions for the CANLIB API.
   Do not use this file in a 16-bit environment.
   
   MATLAB users: if you define WIN32_LEAN_AND_MEAN before including
   this file, you will see a lot less warnings.
 ---------------------------------------------------------------------------
#ifndef _CANLIB_H_
#define _CANLIB_H_
"""

"""
#include <stdlib.h>
#include <windows.h>
#include "canstat.h"
#include "predef.h"
#include "canevt.h"
"""
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

"""
#typedef int canHandle;
"""
class c_canHandle(c_int):
    pass

"""
#define canINVALID_HANDLE      (-1)
"""
canINVALID_HANDLE = -1

"""
#define WM__CANLIB              (WM_USER+16354)
"""

"""
// Flags for canOpenChannel
// 0x01, 0x02, 0x04 are obsolete and reserved.
// The canWANT_xxx names are also obsolete, use canOPEN_xxx instead for new developments.
#define canWANT_EXCLUSIVE           0x0008
#define canWANT_EXTENDED            0x0010
#define canWANT_VIRTUAL             0x0020
#define canOPEN_EXCLUSIVE           canWANT_EXCLUSIVE
#define canOPEN_REQUIRE_EXTENDED    canWANT_EXTENDED
#define canOPEN_ACCEPT_VIRTUAL      canWANT_VIRTUAL
#define canOPEN_OVERRIDE_EXCLUSIVE  0x0040
#define canOPEN_REQUIRE_INIT_ACCESS 0x0080
#define canOPEN_NO_INIT_ACCESS      0x0100
#define canOPEN_ACCEPT_LARGE_DLC    0x0200  // DLC can be greater than 8
"""
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

"""
// Flags for canAccept
#define canFILTER_ACCEPT        1
#define canFILTER_REJECT        2
#define canFILTER_SET_CODE_STD  3
#define canFILTER_SET_MASK_STD  4
#define canFILTER_SET_CODE_EXT  5
#define canFILTER_SET_MASK_EXT  6

#define canFILTER_NULL_MASK     0L
"""
canFILTER_ACCEPT = 1
canFILTER_REJECT = 2
canFILTER_SET_CODE_STD = 3
canFILTER_SET_MASK_STD = 4
canFILTER_SET_CODE_EXT = 5
canFILTER_SET_MASK_EXT = 6

canFILTER_NULL_MASK = 0L

"""
//
// CAN driver types - not all are supported on all cards.
//
#define canDRIVER_NORMAL           4
#define canDRIVER_SILENT           1
#define canDRIVER_SELFRECEPTION    8
#define canDRIVER_OFF              0
// 2,3,5,6,7 are reserved values for compatibility reasons.
"""
canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0

"""
/*
** Common bus speeds. Used in canSetBusParams.
** The values are translated in canlib, canTranslateBaud().
*/
#define canBITRATE_1M        (-1)
#define canBITRATE_500K      (-2)
#define canBITRATE_250K      (-3)
#define canBITRATE_125K      (-4)
#define canBITRATE_100K      (-5)
#define canBITRATE_62K       (-6)
#define canBITRATE_50K       (-7)
#define canBITRATE_83K       (-8)
#define canBITRATE_10K       (-9)
"""
canBITRATE_1M = (-1)
canBITRATE_500K = (-2)
canBITRATE_250K = (-3)
canBITRATE_125K = (-4)
canBITRATE_100K = (-5)
canBITRATE_62K = (-6)
canBITRATE_50K = (-7)
canBITRATE_83K = (-8)
canBITRATE_10K = (-9)

"""
// The BAUD_xxx names are retained for compability.
#define BAUD_1M        (-1)
#define BAUD_500K      (-2)
#define BAUD_250K      (-3)
#define BAUD_125K      (-4)
#define BAUD_100K      (-5)
#define BAUD_62K       (-6)
#define BAUD_50K       (-7)
#define BAUD_83K       (-8)
"""
BAUD_1M = (-1)
BAUD_500K = (-2)
BAUD_250K = (-3)
BAUD_125K = (-4)
BAUD_100K = (-5)
BAUD_62K = (-6)
BAUD_50K = (-7)
BAUD_83K = (-8)

"""
/*
** IOCTL types
*/
#define canIOCTL_PREFER_EXT             1
#define canIOCTL_PREFER_STD             2
// 3,4 reserved.
#define canIOCTL_CLEAR_ERROR_COUNTERS   5
#define canIOCTL_SET_TIMER_SCALE        6
#define canIOCTL_SET_TXACK              7
"""
canIOCTL_PREFER_EXT = 1
canIOCTL_PREFER_STD = 2
canIOCTL_CLEAR_ERROR_COUNTERS = 5
canIOCTL_SET_TIMER_SCALE = 6
canIOCTL_SET_TXACK = 7

"""
#define CANID_METAMSG  (-1L)        // Like msgs containing bus status changes
#define CANID_WILDCARD (-2L)        // We don't care or don't know
"""
CANID_METAMSG = (-1L)
CANID_WILDCARD = (-2L)

"""
//
// Define CANLIBAPI unless it's done already.
// (canlib.c provides its own definitions of CANLIBAPI, DLLIMPORT
// and DLLEXPORT before including this file.)
//
#ifndef CANLIBAPI
#  define CANLIBAPI __stdcall
#  define DLLIMPORT __declspec(dllimport)
#  define DLLEXPORT __declspec(dllexport)
#endif
"""

"""
#ifdef __cplusplus
extern "C" {
#endif
"""

"""
void CANLIBAPI canInitializeLibrary(void);
"""
canInitializeLibrary = canlib32.canInitializeLibrary
canInitializeLibrary.argtypes = []
canInitializeLibrary.restype = None
canInitializeLibrary.errCheck = None

"""
canStatus CANLIBAPI canClose(const int handle);
"""
canClose = canlib32.canClose
canClose.argtypes = [c_int]
canClose.restype = c_canStatus
canClose.errCheck = CheckStatus

"""
canStatus CANLIBAPI canBusOn(const int handle);
"""
canBusOn = canlib32.canBusOn
canBusOn.argtypes = [c_int]
canBusOn.restype = c_canStatus
canBusOn.errCheck = CheckStatus

"""
canStatus CANLIBAPI canBusOff(const int handle);
"""
canBusOff = canlib32.canBusOff
canBusOff.argtypes = [c_int]
canBusOff.restype = c_canStatus
canBusOff.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetBusParams(const int handle,
                           long freq,
                           unsigned int tseg1,
                           unsigned int tseg2,
                           unsigned int sjw,
                           unsigned int noSamp,
                           unsigned int syncmode);
"""
canSetBusParams = canlib32.canSetBusParams
canSetBusParams.argtypes = [c_int, c_long, c_uint, c_uint, c_uint, c_uint,
  c_uint]
canSetBusParams.resType = c_canStatus
canSetBusParams.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetBusParams(const int handle,
                              long * freq,
                              unsigned int * tseg1,
                              unsigned int * tseg2,
                              unsigned int * sjw,
                              unsigned int * noSamp,
                              unsigned int * syncmode);
"""
canGetBusParams = canlib32.canGetBusParams
canGetBusParams.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p, c_void_p]
canGetBusParams.resType = c_canStatus
canGetBusParams.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetBusOutputControl(const int handle,
                                     const unsigned int drivertype);
"""
canSetBusOutputControl = canlib32.canSetBusOutputControl
canSetBusOutputControl.argtypes = [c_int, c_uint]
canSetBusOutputControl.resType = c_canStatus
canSetBusOutputControl.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetBusOutputControl(const int handle,
                                     unsigned int * drivertype);
"""
canGetBusOutputControl = canlib32.canGetBusOutputControl
canGetBusOutputControl.argtypes = [c_int, c_void_p]
canGetBusOutputControl.resType = c_canStatus
canGetBusOutputControl.errCheck = CheckStatus

"""
canStatus CANLIBAPI canAccept(const int handle,
                        const long envelope,
                        const unsigned int flag);
"""
canAccept = canlib32.canAccept
canAccept.argtypes = [c_int, c_long, c_uint]
canAccept.resType = c_canStatus
canAccept.errCheck = CheckStatus

"""
canStatus CANLIBAPI canReadStatus(const int handle,
                            unsigned long * const flags);
"""
canReadStatus = canlib32.canReadStatus
canReadStatus.argtypes = [c_int, c_void_p]
canReadStatus.resType = c_canStatus
canReadStatus.errCheck = CheckStatus

"""
canStatus CANLIBAPI canReadErrorCounters(int handle,
                               unsigned int * txErr,
                               unsigned int * rxErr,
                               unsigned int * ovErr);
"""
canReadErrorCounters = canlib32.canReadErrorCounters
canReadErrorCounters.argtypes = [c_int, c_void_p, c_void_p, c_void_p]
canReadErrorCounters.resType = c_canStatus
canReadErrorCounters.errCheck = CheckStatus

"""
canStatus CANLIBAPI canWrite(int handle, long id, void * msg,
                       unsigned int dlc, unsigned int flag);
"""
canWrite = canlib32.canWrite
canWrite.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint]
canWrite.resType = c_canStatus
canWrite.errCheck = CheckStatus

"""
canStatus CANLIBAPI canWriteSync(int handle, unsigned long timeout);
"""
canWriteSync = canlib32.canWriteSync
canWriteSync.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint]
canWriteSync.resType = c_canStatus
canWriteSync.errCheck = CheckStatus

"""
canStatus CANLIBAPI canRead(int handle,
                      long * id,
                      void * msg,
                      unsigned int * dlc,
                      unsigned int * flag,
                      unsigned long * time);
"""
canRead = canlib32.canRead
canRead.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p, c_void_p]
canRead.resType = c_canStatus
canRead.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canReadWait(int handle,
                          long * id,
                          void * msg,
                          unsigned int * dlc,
                          unsigned int * flag,
                          unsigned long * time,
                          unsigned long timeout);
"""
canReadWait = canlib32.canReadWait
canReadWait.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p,
  c_void_p, c_long]
canReadWait.resType = c_canStatus
canReadWait.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canReadSpecific(int handle, long id, void * msg,
                              unsigned int * dlc, unsigned int * flag,
                              unsigned long * time);
"""
canReadSpecific = canlib32.canReadSpecific
canReadSpecific.argtypes = [c_int, c_long, c_void_p, c_void_p, c_void_p,
  c_void_p]
canReadSpecific.resType = c_canStatus
canReadSpecific.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canReadSync(int handle, unsigned long timeout);
"""
canReadSync = canlib32.canReadSync
canReadSync.argtypes = [c_int, c_ulong]
canReadSync.resType = c_canStatus
canReadSync.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canReadSyncSpecific(int handle, long id, unsigned long timeout);
"""
canReadSyncSpecific = canlib32.canReadSyncSpecific
canReadSyncSpecific.argtypes = [c_int, c_long, c_ulong]
canReadSyncSpecific.resType = c_canStatus
canReadSyncSpecific.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canReadSpecificSkip(int hnd,
                                  long id,
                                  void * msg,
                                  unsigned int * dlc,
                                  unsigned int * flag,
                                  unsigned long * time);
"""
canReadSpecificSkip = canlib32.canReadSpecificSkip
canReadSpecificSkip.argtypes = [c_int, c_long, c_void_p, c_void_p, c_void_p, 
  c_void_p]
canReadSpecificSkip.resType = c_canStatus
canReadSpecificSkip.errCheck = CheckStatusRead

"""
canStatus CANLIBAPI canSetNotify(int handle, HWND aHWnd, unsigned int aNotifyFlags);
"""
canSetNotify = canlib32.canSetNotify
canSetNotify.argtypes = [c_int, c_void_p, c_uint]
canSetNotify.resType = c_canStatus
canSetNotify.errCheck = CheckStatus

"""
canStatus CANLIBAPI canTranslateBaud(long * const freq,
                               unsigned int * const tseg1,
                               unsigned int * const tseg2,
                               unsigned int * const sjw,
                               unsigned int * const nosamp,
                               unsigned int * const syncMode);
"""
canTranslateBaud = canlib32.canTranslateBaud
canTranslateBaud.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, 
  c_void_p]
canTranslateBaud.resType = c_canStatus
canTranslateBaud.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetErrorText(canStatus err, char * buf, unsigned int bufsiz);
"""
canGetErrorText = canlib32.canGetErrorText
canGetErrorText.argtypes = [c_canStatus, c_char_p, c_uint]
canGetErrorText.resType = c_canStatus
canGetErrorText.errCheck = CheckStatus

"""
unsigned short CANLIBAPI canGetVersion(void);
"""
canGetVersion = canlib32.canGetVersion
canGetErrorText.argtypes = []
canGetErrorText.resType = c_ushort
#canGetVersion doesn't return a c_canStatus value, so it has no error checking

"""
canStatus CANLIBAPI canIoCtl(int handle, unsigned int func,
                       void * buf, unsigned int buflen);
"""
canIoCtl = canlib32.canIoCtl
canIoCtl.argtypes = [c_int, c_uint, c_void_p, c_uint]
canIoCtl.resType = c_canStatus
canIoCtl.errCheck = CheckStatus

"""
unsigned long CANLIBAPI canReadTimer(int hnd);
"""
canReadTimer = canlib32.canReadTimer
canReadTimer.argtypes = [c_int]
canReadTimer.resType = c_ulong
#canReadTimer doesn't return a c_canStatus value, so it has no error checking

"""
int CANLIBAPI canOpenChannel(int channel, int flags);
"""
canOpenChannel = canlib32.canOpenChannel
canOpenChannel.argtypes = [c_int, c_int]
canOpenChannel.resType = c_int
#canOpenChannel doesn't return a c_canStatus value, so it has no error checking

"""
canStatus CANLIBAPI canGetNumberOfChannels(int * channelCount);
"""
canGetNumberOfChannels = canlib32.canGetNumberOfChannels
canGetNumberOfChannels.argtypes = [c_void_p]
canGetNumberOfChannels.resType = c_canStatus
canGetNumberOfChannels.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetChannelData(int channel, int item, void *buffer, size_t bufsize);
"""
canGetChannelData = canlib32.canGetChannelData
#TO-DO: is size_t actually a c_int or is it something else?
canGetChannelData.argtypes = [c_int, c_int, c_void_p, c_int]
canGetChannelData.resType = c_canStatus
canGetChannelData.errCheck = CheckStatus

"""
#define canCHANNELDATA_CHANNEL_CAP              1
#define canCHANNELDATA_TRANS_CAP                2
#define canCHANNELDATA_CHANNEL_FLAGS            3   // available, etc
#define canCHANNELDATA_CARD_TYPE                4   // canHWTYPE_xxx
#define canCHANNELDATA_CARD_NUMBER              5   // Number in machine, 0,1,...
#define canCHANNELDATA_CHAN_NO_ON_CARD          6
#define canCHANNELDATA_CARD_SERIAL_NO           7
#define canCHANNELDATA_TRANS_SERIAL_NO          8
#define canCHANNELDATA_CARD_FIRMWARE_REV        9
#define canCHANNELDATA_CARD_HARDWARE_REV        10
#define canCHANNELDATA_CARD_UPC_NO              11
#define canCHANNELDATA_TRANS_UPC_NO             12
#define canCHANNELDATA_CHANNEL_NAME             13
#define canCHANNELDATA_DLL_FILE_VERSION         14
#define canCHANNELDATA_DLL_PRODUCT_VERSION      15
#define canCHANNELDATA_DLL_FILETYPE             16
#define canCHANNELDATA_TRANS_TYPE               17
#define canCHANNELDATA_DEVICE_PHYSICAL_POSITION 18
#define canCHANNELDATA_UI_NUMBER                19
#define canCHANNELDATA_TIMESYNC_ENABLED         20
#define canCHANNELDATA_DRIVER_FILE_VERSION      21
#define canCHANNELDATA_DRIVER_PRODUCT_VERSION   22
#define canCHANNELDATA_MFGNAME_UNICODE          23
#define canCHANNELDATA_MFGNAME_ASCII            24
#define canCHANNELDATA_DEVDESCR_UNICODE         25
#define canCHANNELDATA_DEVDESCR_ASCII           26
#define canCHANNELDATA_DRIVER_NAME              27
"""
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

"""
// channelFlags in canChannelData
#define canCHANNEL_IS_EXCLUSIVE         0x0001
#define canCHANNEL_IS_OPEN              0x0002
"""
canCHANNEL_IS_EXCLUSIVE = 0x0001
canCHANNEL_IS_OPEN = 0x0002

"""
// Hardware types.
#define canHWTYPE_NONE         0        // Unknown
#define canHWTYPE_VIRTUAL      1        // Virtual channel.
#define canHWTYPE_LAPCAN       2        // LAPcan Family
#define canHWTYPE_CANPARI      3        // CANpari (obsolete)
#define canHWTYPE_PCCAN        8        // PCcan Family
#define canHWTYPE_PCICAN       9        // PCIcan Family
#define canHWTYPE_USBCAN      11        // USBcan (obsolete)
#define canHWTYPE_PCICAN_II   40        // PCIcan II family
#define canHWTYPE_USBCAN_II   42        // USBcan II, Memorator et al
#define canHWTYPE_SIMULATED   44        // (obsolete)
#define canHWTYPE_ACQUISITOR  46        // Acquisitor (obsolete)
#define canHWTYPE_LEAF        48        // Kvaser Leaf Family
#define canHWTYPE_PC104_PLUS     50     // PC104+
#define canHWTYPE_PCICANX_II     52     // PCIcanx II
#define canHWTYPE_MEMORATOR_II   54     // Memorator Professional
#define canHWTYPE_MEMORATOR_PRO  54     // Memorator Professional
#define canHWTYPE_USBCAN_PRO  56        // USBcan Professional
#define canHWTYPE_IRIS        58        // Iris
#define canHWTYPE_BLACKBIRD   58        // BlackBird
#define canHWTYPE_MEMORATOR_LIGHT 60    // Memorator Light
"""
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

"""
// Channel capabilities.
#define canCHANNEL_CAP_EXTENDED_CAN         0x00000001L
#define canCHANNEL_CAP_BUS_STATISTICS       0x00000002L
#define canCHANNEL_CAP_ERROR_COUNTERS       0x00000004L
#define canCHANNEL_CAP_CAN_DIAGNOSTICS      0x00000008L
#define canCHANNEL_CAP_GENERATE_ERROR       0x00000010L
#define canCHANNEL_CAP_GENERATE_OVERLOAD    0x00000020L
#define canCHANNEL_CAP_TXREQUEST            0x00000040L
#define canCHANNEL_CAP_TXACKNOWLEDGE        0x00000080L
#define canCHANNEL_CAP_VIRTUAL              0x00010000L
#define canCHANNEL_CAP_SIMULATED            0x00020000L
#define canCHANNEL_CAP_REMOTE               0x00040000L // Remote device, like BlackBird
"""
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

"""
// Driver (transceiver) capabilities
#define canDRIVER_CAP_HIGHSPEED             0x00000001L

#define canIOCTL_GET_RX_BUFFER_LEVEL            8
#define canIOCTL_GET_TX_BUFFER_LEVEL            9
#define canIOCTL_FLUSH_RX_BUFFER                10
#define canIOCTL_FLUSH_TX_BUFFER                11
#define canIOCTL_GET_TIMER_SCALE                12
#define canIOCTL_SET_TXRQ                       13
#define canIOCTL_GET_EVENTHANDLE                14
#define canIOCTL_SET_BYPASS_MODE                15
#define canIOCTL_SET_WAKEUP                     16
#define canIOCTL_GET_DRIVERHANDLE               17
#define canIOCTL_MAP_RXQUEUE                    18
#define canIOCTL_GET_WAKEUP                     19
#define canIOCTL_SET_REPORT_ACCESS_ERRORS       20
#define canIOCTL_GET_REPORT_ACCESS_ERRORS       21
#define canIOCTL_CONNECT_TO_VIRTUAL_BUS         22
#define canIOCTL_DISCONNECT_FROM_VIRTUAL_BUS    23
#define canIOCTL_SET_USER_IOPORT                24
#define canIOCTL_GET_USER_IOPORT                25
#define canIOCTL_SET_BUFFER_WRAPAROUND_MODE     26
#define canIOCTL_SET_RX_QUEUE_SIZE              27
#define canIOCTL_SET_USB_THROTTLE               28
#define canIOCTL_GET_USB_THROTTLE               29
#define canIOCTL_SET_BUSON_TIME_AUTO_RESET      30
"""
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

"""
// For canIOCTL_xxx_USER_IOPORT
typedef struct {
  unsigned int portNo;
  unsigned int portValue;
} canUserIoPortData;
"""
class c_canUserIOPortData(Structure):
    _fields_ = [("portNo", c_uint), ("portValue", c_uint)]

"""
canStatus CANLIBAPI canWaitForEvent(int hnd, DWORD timeout);
"""
canWaitForEvent = canlib32.canWaitForEvent
canWaitForEvent.argtypes = [c_int, c_ulong]
canWaitForEvent.resType = c_canStatus
canWaitForEvent.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetBusParamsC200(int hnd, BYTE btr0, BYTE btr1);
"""
canSetBusParamsC200 = canlib32.canSetBusParamsC200
canSetBusParamsC200.argtypes = [c_int, c_ubyte, c_ubyte]
canSetBusParamsC200.resType = c_canStatus
canSetBusParamsC200.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetDriverMode(int hnd, int lineMode, int resNet);
"""
canSetDriverMode = canlib32.canSetDriverMode
canSetDriverMode.argtypes = [c_int, c_int, c_int]
canSetDriverMode.resType = c_canStatus
canSetDriverMode.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetDriverMode(int hnd, int *lineMode, int *resNet);
"""
canGetDriverMode = canlib32.canGetDriverMode
canGetDriverMode.argtypes = [c_int, c_void_p, c_void_p]
canGetDriverMode.resType = c_canStatus
canGetDriverMode.errCheck = CheckStatus

"""
// Item codes for canGetVersionEx()
#define canVERSION_CANLIB32_VERSION     0
#define canVERSION_CANLIB32_PRODVER     1
#define canVERSION_CANLIB32_PRODVER32   2
#define canVERSION_CANLIB32_BETA        3
"""
canVERSION_CANLIB32_VERSION = 0
canVERSION_CANLIB32_PRODVER = 1
canVERSION_CANLIB32_PRODVER32 = 2
canVERSION_CANLIB32_BETA = 3

"""
unsigned int CANLIBAPI canGetVersionEx(unsigned int itemCode);
"""
canGetVersionEx = canlib32.canGetVersionEx
canGetVersionEx.argtypes = [c_uint]
canGetVersionEx.restype = c_uint
#canGetVersionEx doesn't return a c_canStatus value, so it has no error
#checking

"""
canStatus CANLIBAPI canParamGetCount (void);
"""
canParamGetCount = canlib32.canParamGetCount
canParamGetCount.argtypes = []
canParamGetCount.resType = c_canStatus
canParamGetCount.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamCommitChanges (void);
"""
canParamCommitChanges = canlib32.canParamCommitChanges
canParamCommitChanges.argtypes = []
canParamCommitChanges.resType = c_canStatus
canParamCommitChanges.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamDeleteEntry (int index);
"""
canParamDeleteEntry = canlib32.canParamDeleteEntry
canParamDeleteEntry.argtypes = [c_int]
canParamDeleteEntry.resType = c_canStatus
canParamDeleteEntry.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamCreateNewEntry (void);
"""
canParamCreateNewEntry = canlib32.canParamCreateNewEntry
canParamCreateNewEntry.argtypes = []
canParamCreateNewEntry.resType = c_canStatus
canParamCreateNewEntry.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamSwapEntries (int index1, int index2);
"""
canParamSwapEntries = canlib32.canParamSwapEntries
canParamSwapEntries.argtypes = [c_int, c_int]
canParamSwapEntries.resType = c_canStatus
canParamSwapEntries.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamGetName (int index, char *buffer, int maxlen);
"""
canParamGetName = canlib32.canParamGetName
canParamGetName.argtypes = [c_int, c_char_p, c_int]
canParamGetName.resType = c_canStatus
canParamGetName.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamGetChannelNumber (int index);
"""
canParamGetChannelNumber = canlib32.canParamGetChannelNumber
canParamGetChannelNumber.argtypes = [c_int]
canParamGetChannelNumber.resType = c_canStatus
canParamGetChannelNumber.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamGetBusParams (int index,
                                          long* bitrate,
                                          unsigned int *tseg1,
                                          unsigned int *tseg2,
                                          unsigned int *sjw,
                                          unsigned int *noSamp);
"""
canParamGetBusParams = canlib32.canParamGetBusParams
canParamGetBusParams.argtypes = [c_int, c_void_p, c_void_p, c_void_p, c_void_p, 
  c_void_p]
canParamGetBusParams.resType = c_canStatus
canParamGetBusParams.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamSetName (int index, const char *buffer);
"""
canParamSetName = canlib32.canParamSetName
canParamSetName.argtypes = [c_int, c_char_p]
canParamSetName.resType = c_canStatus
canParamSetName.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamSetChannelNumber (int index, int channel);
"""
canParamSetChannelNumber = canlib32.canParamSetChannelNumber
canParamSetChannelNumber.argtypes = [c_int, c_int]
canParamSetChannelNumber.resType = c_canStatus
canParamSetChannelNumber.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamSetBusParams (int index,
                                          long bitrate,
                                          unsigned int tseg1,
                                          unsigned int tseg2,
                                          unsigned int sjw,
                                          unsigned int noSamp);
"""
canParamSetBusParams = canlib32.canParamSetBusParams
canParamSetBusParams.argtypes = [c_int, c_long, c_uint, c_uint, c_uint, c_uint]
canParamSetBusParams.resType = c_canStatus
canParamSetBusParams.errCheck = CheckStatus

"""
canStatus CANLIBAPI canParamFindByName (const char *name);
"""
canParamFindByName = canlib32.canParamFindByName
canParamFindByName.argtypes = [c_char_p]
canParamFindByName.resType = c_canStatus
canParamFindByName.errCheck = CheckStatus

"""
// Frees all object buffers associated with the specified handle.
canStatus CANLIBAPI canObjBufFreeAll(int handle);
"""
canObjBufFreeAll = canlib32.canObjBufFreeAll
canObjBufFreeAll.argtypes = [c_int]
canObjBufFreeAll.resType = c_canStatus
canObjBufFreeAll.errCheck = CheckStatus

"""
// Allocates an object buffer of the specified type.
canStatus CANLIBAPI canObjBufAllocate(int handle, int type);
"""
canObjBufAllocate = canlib32.canObjBufAllocate
canObjBufAllocate.argtypes = [c_int, c_int]
canObjBufAllocate.resType = c_canStatus
canObjBufAllocate.errCheck = CheckStatus

"""
#define canOBJBUF_TYPE_AUTO_RESPONSE            0x01
#define canOBJBUF_TYPE_PERIODIC_TX              0x02
"""
canOBJBUF_TYPE_AUTO_RESPONSE = 0x01
canOBJBUF_TYPE_PERIODIC_TX = 0x02

"""
// Deallocates the object buffer with the specified index.
canStatus CANLIBAPI canObjBufFree(int handle, int idx);
"""
canObjBufFree = canlib32.canObjBufFree
canObjBufFree.argtypes = [c_int, c_int]
canObjBufFree.resType = c_canStatus
canObjBufFree.errCheck = CheckStatus

"""
// Writes CAN data to the object buffer with the specified index.
canStatus CANLIBAPI canObjBufWrite(int handle, int idx, int id, void* msg,
                                   unsigned int dlc, unsigned int flags);
"""
canObjBufWrite = canlib32.canObjBufWrite
canObjBufWrite.argtypes = [c_int, c_int, c_int, c_void_p, c_uint, c_uint]
canObjBufWrite.resType = c_canStatus
canObjBufWrite.errCheck = CheckStatus

"""
// For an AUTO_RESPONSE buffer, set the code and mask that together define
// the identifier(s) that trigger(s) the automatic response.
canStatus CANLIBAPI canObjBufSetFilter(int handle, int idx,
                                       unsigned int code, unsigned int mask);
"""
canObjBufSetFilter = canlib32.canObjBufSetFilter
canObjBufSetFilter.argtypes = [c_int, c_int, c_uint, c_uint]
canObjBufSetFilter.resType = c_canStatus
canObjBufSetFilter.errCheck = CheckStatus

"""
// Sets buffer-speficic flags.
canStatus CANLIBAPI canObjBufSetFlags(int handle, int idx, unsigned int flags);
"""
canObjBufSetFlags = canlib32.canObjBufSetFlags
canObjBufSetFlags.argtypes = [c_int, c_int, c_uint]
canObjBufSetFlags.resType = c_canStatus
canObjBufSetFlags.errCheck = CheckStatus

"""
// The buffer responds to RTRs only, not regular messages.
// AUTO_RESPONSE buffers only
#define canOBJBUF_AUTO_RESPONSE_RTR_ONLY        0x01
"""
canOBJBUF_AUTO_RESPONSE_RTR_ONLY = 0x01

"""
// Sets transmission period for auto tx buffers.
canStatus CANLIBAPI canObjBufSetPeriod(int hnd, int idx, unsigned int period);
"""
canObjBufSetPeriod = canlib32.canObjBufSetPeriod
canObjBufSetPeriod.argtypes = [c_int, c_int, c_uint]
canObjBufSetPeriod.resType = c_canStatus
canObjBufSetPeriod.errCheck = CheckStatus

"""
// Sets message count for auto tx buffers.
canStatus CANLIBAPI canObjBufSetMsgCount(int hnd, int idx, unsigned int count);
"""
canObjBufSetMsgCount = canlib32.canObjBufSetMsgCount
canObjBufSetMsgCount.argtypes = [c_int, c_int, c_uint]
canObjBufSetMsgCount.resType = c_canStatus
canObjBufSetMsgCount.errCheck = CheckStatus

"""
// Enable object buffer with index idx.
canStatus CANLIBAPI canObjBufEnable(int handle, int idx);
"""
canObjBufEnable = canlib32.canObjBufEnable
canObjBufEnable.argtypes = [c_int, c_int]
canObjBufEnable.resType = c_canStatus
canObjBufEnable.errCheck = CheckStatus

"""
// Disable object buffer with index idx.
canStatus CANLIBAPI canObjBufDisable(int handle, int idx);
"""
canObjBufDisable = canlib32.canObjBufDisable
canObjBufDisable.argtypes = [c_int, c_int]
canObjBufDisable.resType = c_canStatus
canObjBufDisable.errCheck = CheckStatus

"""
// For certain diagnostics.
canStatus CANLIBAPI canObjBufSendBurst(int hnd, int idx, unsigned int burstlen);
"""
canObjBufSendBurst = canlib32.canObjBufSendBurst
canObjBufSendBurst.argtypes = [c_int, c_int, c_uint]
canObjBufSendBurst.resType = c_canStatus
canObjBufSendBurst.errCheck = CheckStatus

"""
#define canVERSION_DONT_ACCEPT_LATER      0x01
#define canVERSION_DONT_ACCEPT_BETAS      0x02
"""
canVERSION_DONT_ACCEPT_LATER = 0x01
canVERSION_DONT_ACCEPT_BETAS = 0x02

"""
// Check for specific version(s) of CANLIB.
BOOL CANLIBAPI canProbeVersion(int hnd, int major, int minor, int oem_id, unsigned int flags);
"""
canProbeVersion = canlib32.canProbeVersion
canProbeVersion.argtypes = [c_int, c_int, c_int, c_int, c_uint]
canProbeVersion.resType = c_bool
#canProbeVersion doesn't return a c_canStatus value, so it has no error checking

"""
// Try to "reset" the CAN bus.
canStatus CANLIBAPI canResetBus(int handle);
"""
canResetBus = canlib32.canResetBus
canResetBus.argtypes = [c_int]
canResetBus.resType = c_canStatus
canResetBus.errCheck = CheckStatus

"""
// Convenience function that combines canWrite and canWriteSync.
canStatus CANLIBAPI canWriteWait(int handle, long id, void * msg,
                                 unsigned int dlc, unsigned int flag,
                                 unsigned long timeout);
"""
canWriteWait = canlib32.canWriteWait
canWriteWait.argtypes = [c_int, c_long, c_void_p, c_uint, c_uint, c_ulong]
canWriteWait.resType = c_canStatus
canWriteWait.errCheck = CheckStatus

"""
// Tell canlib32.dll to unload its DLLs.
canStatus CANLIBAPI canUnloadLibrary(void);
"""
canUnloadLibrary = canlib32.canUnloadLibrary
canUnloadLibrary.argtypes = []
canUnloadLibrary.resType = c_canStatus
canUnloadLibrary.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetAcceptanceFilter(int hnd, unsigned int code,
                                           unsigned int mask, int is_extended);
"""
canSetAcceptanceFilter = canlib32.canSetAcceptanceFilter
canSetAcceptanceFilter.argtypes = [c_int, c_uint, c_uint, c_int]
canSetAcceptanceFilter.resType = c_canStatus
canSetAcceptanceFilter.errCheck = CheckStatus

"""
canStatus CANLIBAPI canFlushReceiveQueue(int hnd);
"""
canFlushReceiveQueue = canlib32.canFlushReceiveQueue
canFlushReceiveQueue.argtypes = [c_int]
canFlushReceiveQueue.resType = c_canStatus
canFlushReceiveQueue.errCheck = CheckStatus

"""
canStatus CANLIBAPI canFlushTransmitQueue(int hnd);
"""
canFlushTransmitQueue = canlib32.canFlushTransmitQueue
canFlushTransmitQueue.argtypes = [c_int]
canFlushTransmitQueue.resType = c_canStatus
canFlushTransmitQueue.errCheck = CheckStatus

"""
canStatus CANLIBAPI kvGetApplicationMapping(int busType,
                                  char *appName,
                                  int appChannel,
                                  int *resultingChannel);
"""
kvGetApplicationMapping = canlib32.kvGetApplicationMapping
kvGetApplicationMapping.argtypes = [c_int, c_char_p, c_int, c_void_p]
kvGetApplicationMapping.resType = c_canStatus
kvGetApplicationMapping.errCheck = CheckStatus

"""
canStatus CANLIBAPI kvBeep(int hnd, int freq, unsigned int duration);
"""
kvBeep = canlib32.kvBeep
kvBeep.argtypes = [c_int, c_int, c_uint]
kvBeep.resType = c_canStatus
kvBeep.errCheck = CheckStatus

"""
canStatus CANLIBAPI kvSelfTest(int hnd, unsigned long *presults);
"""
kvSelfTest = canlib32.kvSelfTest
kvSelfTest.argtypes = [c_int, c_void_p]
kvSelfTest.resType = c_canStatus
kvSelfTest.errCheck = CheckStatus

"""
#define kvLED_ACTION_ALL_LEDS_ON    0
#define kvLED_ACTION_ALL_LEDS_OFF   1  
#define kvLED_ACTION_LED_0_ON       2
#define kvLED_ACTION_LED_0_OFF      3
#define kvLED_ACTION_LED_1_ON       4
#define kvLED_ACTION_LED_1_OFF      5
#define kvLED_ACTION_LED_2_ON       6
#define kvLED_ACTION_LED_2_OFF      7
#define kvLED_ACTION_LED_3_ON       8
#define kvLED_ACTION_LED_3_OFF      9
"""
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

"""
canStatus CANLIBAPI kvFlashLeds(int hnd, int action, int timeout);
"""
kvFlashLeds = canlib32.kvFlashLeds
kvFlashLeds.argtypes = [c_int, c_int, c_int]
kvFlashLeds.resType = c_canStatus
kvFlashLeds.errCheck = CheckStatus

"""
canStatus CANLIBAPI canRequestChipStatus(int hnd);
"""
canRequestChipStatus = canlib32.canRequestChipStatus
canRequestChipStatus.argtypes = [c_int]
canRequestChipStatus.resType = c_canStatus
canRequestChipStatus.errCheck = CheckStatus

"""
canStatus CANLIBAPI canRequestBusStatistics(int hnd);
"""
canRequestBusStatistics = canlib32.canRequestBusStatistics
canRequestBusStatistics.argtypes = [c_int]
canRequestBusStatistics.resType = c_canStatus
canRequestBusStatistics.errCheck = CheckStatus

"""
typedef struct canBusStatistics_s {
  unsigned long  stdData;
  unsigned long  stdRemote;
  unsigned long  extData;
  unsigned long  extRemote;
  unsigned long  errFrame;      // Error frames
  unsigned long  busLoad;       // 0 .. 10000 meaning 0.00-100.00%
  unsigned long  overruns;
} canBusStatistics;
"""
class c_canBusStatistics(Structure):
    _fields_ = [("stdData", c_ulong), ("stdRemote", c_ulong),
      ("extData", c_ulong), ("extRemote", c_ulong), ("errFrame", c_ulong),
      ("busLoad", c_ulong), ("overruns", c_ulong)]

"""
canStatus CANLIBAPI canGetBusStatistics(int hnd, canBusStatistics *stat, size_t bufsiz);
"""
canGetBusStatistics = canlib32.canGetBusStatistics
canGetBusStatistics.argtypes = [c_int, c_void_p, c_int]#TO-DO: is size_t a c_int?
canGetBusStatistics.resType = c_canStatus
canGetBusStatistics.errCheck = CheckStatus

"""
canStatus CANLIBAPI canSetBitrate(int hnd, int bitrate);
"""
canSetBitrate = canlib32.canSetBitrate
canSetBitrate.argtypes = [c_int, c_int]
canSetBitrate.resType = c_canStatus
canSetBitrate.errCheck = CheckStatus

"""
canStatus CANLIBAPI kvAnnounceIdentity(int hnd, void *buf, size_t bufsiz);
"""
kvAnnounceIdentity = canlib32.kvAnnounceIdentity
kvAnnounceIdentity.argtypes = [c_int, c_void_p, c_int]#TO-DO: is size_t a c_int?
kvAnnounceIdentity.resType = c_canStatus
kvAnnounceIdentity.errCheck = CheckStatus

"""
canStatus CANLIBAPI canGetHandleData(int hnd, int item, void *buffer, size_t bufsize);
"""
canGetHandleData = canlib32.canGetHandleData
canGetHandleData.argtypes = [c_int, c_int, c_void_p, c_int]#TO-DO: is size_t a c_int?
canGetHandleData.resType = c_canStatus
canGetHandleData.errCheck = CheckStatus

"""
typedef void *kvTimeDomain;
"""
class c_kvTimeDomain(c_void_p):
    pass

"""
typedef canStatus kvStatus;
"""
class c_kvStatus(c_canStatus):
    pass

"""
typedef struct kvTimeDomainData_s {
  int nMagiSyncGroups;
  int nMagiSyncedMembers;
  int nNonMagiSyncCards;
  int nNonMagiSyncedMembers;
} kvTimeDomainData;
"""
class c_kvTimeDomainData(Structure):
    _fields_ = [("nMagiSyncGroups", c_int), ("nMagiSyncedMembers", c_int),
      ("nNonMagiSyncCards", c_int), ("nNonMagiSyncedMembers", c_int)]

"""
kvStatus CANLIBAPI kvTimeDomainCreate(kvTimeDomain *domain);
"""
kvTimeDomainCreate = canlib32.kvTimeDomainCreate
kvTimeDomainCreate.argtypes = [c_kvTimeDomain]
kvTimeDomainCreate.resType = c_kvStatus
kvTimeDomainCreate.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvTimeDomainDelete(kvTimeDomain domain);
"""
kvTimeDomainDelete = canlib32.kvTimeDomainDelete
kvTimeDomainDelete.argtypes = [c_kvTimeDomain]
kvTimeDomainDelete.resType = c_kvStatus
kvTimeDomainDelete.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvTimeDomainResetTime(kvTimeDomain domain);
"""
kvTimeDomainResetTime = canlib32.kvTimeDomainResetTime
kvTimeDomainResetTime.argtypes = [c_kvTimeDomain]
kvTimeDomainResetTime.resType = c_kvStatus
kvTimeDomainResetTime.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvTimeDomainGetData(kvTimeDomain domain, kvTimeDomainData *data, size_t bufsiz);
"""
kvTimeDomainGetData = canlib32.kvTimeDomainGetData
kvTimeDomainGetData.argtypes = [c_kvTimeDomain, c_void_p, c_int]#TO-DO: is size_t a c_int?
kvTimeDomainGetData.resType = c_kvStatus
kvTimeDomainGetData.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvTimeDomainAddHandle(kvTimeDomain domain, int handle);
"""
kvTimeDomainAddHandle = canlib32.kvTimeDomainAddHandle
kvTimeDomainAddHandle.argtypes = [c_kvTimeDomain, c_int]
kvTimeDomainAddHandle.resType = c_kvStatus
kvTimeDomainAddHandle.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvTimeDomainRemoveHandle(kvTimeDomain domain, int handle);
"""
kvTimeDomainRemoveHandle = canlib32.kvTimeDomainRemoveHandle
kvTimeDomainRemoveHandle.argtypes = [c_kvTimeDomain, c_int]
kvTimeDomainRemoveHandle.resType = c_kvStatus
kvTimeDomainRemoveHandle.errCheck = CheckStatus

"""
typedef void (CANLIBAPI *kvCallback_t)(int handle, void* context, unsigned int notifyEvent);
"""
class c_kvCallback(c_void_p):
    pass

CALLBACKFUNC = CFUNCTYPE(c_int, c_int)

"""
kvStatus CANLIBAPI kvSetNotifyCallback(int hnd, kvCallback_t callback, void* context, unsigned int notifyFlags);
"""
kvSetNotifyCallback = canlib32.kvSetNotifyCallback
kvSetNotifyCallback.argtypes = [c_int, c_kvCallback, c_void_p, c_uint]
kvSetNotifyCallback.resType = c_kvStatus
kvSetNotifyCallback.errCheck = CheckStatus

"""
#define kvBUSTYPE_NONE          0
#define kvBUSTYPE_PCI           1
#define kvBUSTYPE_PCMCIA        2
#define kvBUSTYPE_USB           3
#define kvBUSTYPE_WLAN          4
#define kvBUSTYPE_PCI_EXPRESS   5
#define kvBUSTYPE_ISA           6
#define kvBUSTYPE_VIRTUAL       7
#define kvBUSTYPE_PC104_PLUS    8
"""
kvBUSTYPE_NONE = 0
kvBUSTYPE_PCI = 1
kvBUSTYPE_PCMCIA = 2
kvBUSTYPE_USB = 3
kvBUSTYPE_WLAN = 4
kvBUSTYPE_PCI_EXPRESS = 5
kvBUSTYPE_ISA = 6
kvBUSTYPE_VIRTUAL = 7
kvBUSTYPE_PC104_PLUS = 8

"""
kvStatus CANLIBAPI kvGetSupportedInterfaceInfo(int index, char *hwName, size_t nameLen, int *hwType, int *hwBusType);
"""
kvGetSupportedInterfaceInfo = canlib32.kvGetSupportedInterfaceInfo
kvGetSupportedInterfaceInfo.argtypes = [c_int, c_char_p, c_int, c_void_p, c_void_p]
kvGetSupportedInterfaceInfo.resType = c_kvStatus
kvGetSupportedInterfaceInfo.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvReadTimer(int hnd, unsigned int *time);
"""
kvReadTimer = canlib32.kvReadTimer
kvReadTimer.argtypes = [c_int, c_void_p]
kvReadTimer.resType = c_kvStatus
kvReadTimer.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvReadTimer64(int hnd, KVINT64 *time);
"""
kvReadTimer64 = canlib32.kvReadTimer64
kvReadTimer64.argtypes = [c_int, c_void_p]
kvReadTimer64.resType = c_kvStatus
kvReadTimer64.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvReadDeviceCustomerData(int hnd, int userNumber, int itemNumber, void *data, size_t bufsiz);
"""
kvReadDeviceCustomerData = canlib32.kvReadDeviceCustomerData
kvReadDeviceCustomerData.argtypes = [c_int, c_int, c_int, c_void_p, c_int]#TO-DO: is size_t a c_int?
kvReadDeviceCustomerData.resType = c_kvStatus
kvReadDeviceCustomerData.errCheck = CheckStatus

"""
//
// APIs for t-script
// 
"""

"""
#define ENVVAR_TYPE_INT       1
#define ENVVAR_TYPE_FLOAT     2
#define ENVVAR_TYPE_STRING    3
"""
ENVVAR_TYPE_INT = 1
ENVVAR_TYPE_FLOAT = 2
ENVVAR_TYPE_STRING = 3

"""
typedef __int64 kvEnvHandle;
"""
class c_kvEnvHandle(c_longlong):
    pass

"""
kvStatus CANLIBAPI kvScriptStart(int hnd, int scriptNo); 
"""
kvScriptStart = canlib32.kvScriptStart
kvScriptStart.argtypes = [c_int, c_int]
kvScriptStart.resType = c_kvStatus
kvScriptStart.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvScriptStop(int hnd, int scriptNo); 
"""
kvScriptStop = canlib32.kvScriptStop
kvScriptStop.argtypes = [c_int, c_int]
kvScriptStop.resType = c_kvStatus
kvScriptStop.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvScriptForceStop(int hnd, int scriptNo);
"""
kvScriptForceStop = canlib32.kvScriptForceStop
kvScriptForceStop.argtypes = [c_int, c_int]
kvScriptForceStop.resType = c_kvStatus
kvScriptForceStop.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvScriptSendEvent(int hnd, int scriptNo, int eventNo, int data);
"""
kvScriptSendEvent = canlib32.kvScriptSendEvent
kvScriptSendEvent.argtypes = [c_int, c_int, c_int, c_int]
kvScriptSendEvent.resType = c_kvStatus
kvScriptSendEvent.errCheck = CheckStatus

"""
kvEnvHandle CANLIBAPI kvScriptEnvvarOpen(int hnd, char* envvarName, int scriptNo, int *envvarType, int *envvarSize); // returns scriptHandle
"""
kvScriptEnvvarOpen = canlib32.kvScriptEnvvarOpen
kvScriptEnvvarOpen.argtypes = [c_int, c_char_p, c_int, c_void_p, c_void_p]
kvScriptEnvvarOpen.resType = c_kvEnvHandle
#Since kvScriptEnvvarOpen doesn't return a status value, it has no error checking

"""
kvStatus     CANLIBAPI kvScriptEnvvarClose(kvEnvHandle eHnd);
"""
kvScriptEnvvarClose = canlib32.kvScriptEnvvarClose
kvScriptEnvvarClose.argtypes = [c_kvEnvHandle]
kvScriptEnvvarClose.resType = c_kvStatus
kvScriptEnvvarClose.errCheck = CheckStatus

"""
kvStatus     CANLIBAPI kvScriptEnvvarSetInt(kvEnvHandle eHnd, int val);
"""
kvScriptEnvvarSetInt = canlib32.kvScriptEnvvarSetInt
kvScriptEnvvarSetInt.argtypes = [c_kvEnvHandle, c_int]
kvScriptEnvvarSetInt.resType = c_kvStatus
kvScriptEnvvarSetInt.errCheck = CheckStatus

"""
kvStatus     CANLIBAPI kvScriptEnvvarGetInt(kvEnvHandle eHnd, int *val);
"""
kvScriptEnvvarGetInt = canlib32.kvScriptEnvvarGetInt
kvScriptEnvvarGetInt.argtypes = [c_kvEnvHandle, c_void_p]
kvScriptEnvvarGetInt.resType = c_kvStatus
kvScriptEnvvarGetInt.errCheck = CheckStatus

"""
kvStatus     CANLIBAPI kvScriptEnvvarSetData(kvEnvHandle eHnd, unsigned char *buf, int start_index, int data_len);
"""
kvScriptEnvvarSetData = canlib32.kvScriptEnvvarSetData
kvScriptEnvvarSetData.argtypes = [c_kvEnvHandle, c_void_p, c_int, c_int]
kvScriptEnvvarSetData.resType = c_kvStatus
kvScriptEnvvarSetData.errCheck = CheckStatus

"""
kvStatus     CANLIBAPI kvScriptEnvvarGetData(kvEnvHandle eHnd, unsigned char *buf, int start_index, int data_len);
"""
kvScriptEnvvarGetData = canlib32.kvScriptEnvvarGetData
kvScriptEnvvarGetData.argtypes = [c_kvEnvHandle, c_void_p, c_int, c_int]
kvScriptEnvvarGetData.resType = c_kvStatus
kvScriptEnvvarGetData.errCheck = CheckStatus

"""
kvStatus     CANLIBAPI kvScriptGetMaxEnvvarSize(int hnd, int *envvarSize);
"""
kvScriptGetMaxEnvvarSize = canlib32.kvScriptGetMaxEnvvarSize
kvScriptGetMaxEnvvarSize.argtypes = [c_int, c_void_p]
kvScriptGetMaxEnvvarSize.resType = c_kvStatus
kvScriptGetMaxEnvvarSize.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvScriptLoadFileOnDevice(int hnd, int scriptNo, char *localFile);
"""
kvScriptLoadFileOnDevice = canlib32.kvScriptLoadFileOnDevice
kvScriptLoadFileOnDevice.argtypes = [c_int, c_int, c_char_p]
kvScriptLoadFileOnDevice.resType = c_kvStatus
kvScriptLoadFileOnDevice.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvScriptLoadFile(int hnd, int scriptNo, char *filePathOnPC);
"""
kvScriptLoadFile = canlib32.kvScriptLoadFile
kvScriptLoadFile.argtypes = [c_int, c_int, c_char_p]
kvScriptLoadFile.resType = c_kvStatus
kvScriptLoadFile.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvFileCopyToDevice(int hnd, char *hostFileName, char *deviceFileName);
"""
kvFileCopyToDevice = canlib32.kvFileCopyToDevice
kvFileCopyToDevice.argtypes = [c_int, c_int, c_char_p]
kvFileCopyToDevice.resType = c_kvStatus
kvFileCopyToDevice.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvFileCopyFromDevice(int hnd, char *deviceFileName, char *hostFileName);
"""
kvFileCopyFromDevice = canlib32.kvFileCopyFromDevice
kvFileCopyFromDevice.argtypes = [c_int, c_char_p, c_char_p]
kvFileCopyFromDevice.resType = c_kvStatus
kvFileCopyFromDevice.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvFileDelete(int hnd, char *deviceFileName);
"""
kvFileDelete = canlib32.kvFileDelete
kvFileDelete.argtypes = [c_int, c_char_p]
kvFileDelete.resType = c_kvStatus
kvFileDelete.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvFileGetFileData(int hnd, int fileNo, ... );                 // return list with names, sizes, optional checksums
"""
#TO-DO: "..."?

"""
kvStatus CANLIBAPI kvGetFileCount(int hnd, int *count);                          // return number of files
"""
#TO-DO: does not exist in CANLIB 4.1
#kvGetFileCount = canlib32.kvGetFileCount
#kvGetFileCount.argtypes = [c_int, c_void_p]
#kvGetFileCount.resType = c_kvStatus
#kvGetFileCount.errCheck = CheckStatus

"""
kvStatus CANLIBAPI kvFileGetSystemData(int hnd, int itemCode, int *result);
"""
kvFileGetSystemData = canlib32.kvFileGetSystemData
kvFileGetSystemData.argtypes = [c_int, c_int, c_void_p]
kvFileGetSystemData.resType = c_kvStatus
kvFileGetSystemData.errCheck = CheckStatus

"""
//
"""

#################################TO-DO#################################
"""
//
// The following functions are not yet implemented. Do not use them.
//
"""

"""
canStatus CANLIBAPI canReadEvent(int hnd, CanEvent *event);
"""

"""
void CANLIBAPI canSetDebug(int d);
"""

"""
canStatus CANLIBAPI canSetNotifyEx(int handle, HANDLE event, unsigned int flags);
"""

"""
canStatus CANLIBAPI canSetTimer(int hnd, DWORD interval, DWORD flags);
"""

"""
#define canTIMER_CYCLIC             0x01
#define canTIMER_EXPENSIVE          0x02
"""
canTIMER_CYCLIC = 0x01
canTIMER_EXPENSIVE = 0x02

"""
int CANLIBAPI canSplitHandle(int hnd, int channel);
"""

"""
int CANLIBAPI canOpenMultiple(DWORD bitmask, int flags);
"""

###############################end TO-DO###############################

"""
#ifdef __cplusplus
}
#endif

#include "obsolete.h"

#endif
"""

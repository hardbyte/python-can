"""
/*
**                   Copyright 1995-2004 by KVASER AB, SWEDEN      
**                        WWW: http://www.kvaser.com
**
** This software is furnished under a license and may be used and copied
** only in accordance with the terms of such license.
**
** Description:
**   Thsi file defines status codes for canlib.
** ---------------------------------------------------------------------------
*/
#ifndef _CANSTAT_H_
#define _CANSTAT_H_
"""

from ctypes import *

"""
//
// Don't forget to update canGetErrorText in canlib.c if this is changed!
//
typedef enum {
    canOK                  = 0,
    canERR_PARAM           = -1,     // Error in parameter
    canERR_NOMSG           = -2,     // No messages available
    canERR_NOTFOUND        = -3,     // Specified hw not found
    canERR_NOMEM           = -4,     // Out of memory
    canERR_NOCHANNELS      = -5,     // No channels avaliable
    canERR_RESERVED_3      = -6,
    canERR_TIMEOUT         = -7,     // Timeout occurred
    canERR_NOTINITIALIZED  = -8,     // Lib not initialized
    canERR_NOHANDLES       = -9,     // Can't get handle
    canERR_INVHANDLE       = -10,    // Handle is invalid
    canERR_INIFILE         = -11,    // Error in the ini-file (16-bit only)
    canERR_DRIVER          = -12,    // CAN driver type not supported
    canERR_TXBUFOFL        = -13,    // Transmit buffer overflow
    canERR_RESERVED_1      = -14,
    canERR_HARDWARE        = -15,    // Some hardware error has occurred
    canERR_DYNALOAD        = -16,    // Can't find requested DLL
    canERR_DYNALIB         = -17,    // DLL seems to be wrong version
    canERR_DYNAINIT        = -18,    // Error when initializing DLL
    canERR_NOT_SUPPORTED   = -19,    // Operation not supported by hardware or firmware
    canERR_RESERVED_5      = -20,
    canERR_RESERVED_6      = -21,
    canERR_RESERVED_2      = -22,
    canERR_DRIVERLOAD      = -23,    // Can't find/load driver
    canERR_DRIVERFAILED    = -24,    // DeviceIOControl failed; use Win32 GetLastError()
    canERR_NOCONFIGMGR     = -25,    // Can't find req'd config s/w (e.g. CS/SS)
    canERR_NOCARD          = -26,    // The card was removed or not inserted
    canERR_RESERVED_7      = -27,
    canERR_REGISTRY        = -28,    // Error in the Registry
    canERR_LICENSE         = -29,    // The license is not valid.
    canERR_INTERNAL        = -30,    // Internal error in the driver.
    canERR_NO_ACCESS       = -31,    // Access denied
    canERR_NOT_IMPLEMENTED = -32,    // Requested function is not implemented

    // The last entry - a dummy so we know where NOT to place a comma.
    canERR__RESERVED       = -33
} canStatus;
"""
class c_canStatus(c_int):
    pass

canOK = 0
canERR_PARAM = -1
canERR_NOMSG = -2
canERR_NOTFOUND = -3
canERR_NOMEM = -4
canERR_NOCHANNELS = -5
canERR_RESERVED_3 = -6
canERR_TIMEOUT = -7
canERR_NOTINITIALIZED = -8
canERR_NOHANDLES = -9
canERR_INVHANDLE = -10
canERR_INIFILE = -11
canERR_DRIVER = -12
canERR_TXBUFOFL = -13
canERR_RESERVED_1 = -14
canERR_HARDWARE = -15
canERR_DYNALOAD = -16
canERR_DYNALIB = -17
canERR_DYNAINIT = -18
canERR_NOT_SUPPORTED = -19
canERR_RESERVED_5 = -20
canERR_RESERVED_6 = -21
canERR_RESERVED_2 = -22
canERR_DRIVERLOAD = -23
canERR_DRIVERFAILED = -24
canERR_NOCONFIGMGR = -25
canERR_NOCARD = -26
canERR_RESERVED_7 = -27
canERR_REGISTRY = -28
canERR_LICENSE = -29
canERR_INTERNAL = -30
canERR_NO_ACCESS = -31
canERR_NOT_IMPLEMENTED = -32
canERR__RESERVED       = -33

"""
#define CANSTATUS_SUCCESS(X) ((X) == canOK)
"""
def CANSTATUS_SUCCESS(status):
    if status.value == canOK:
        return True
    else:
        return False

"""
#define CANSTATUS_FAILURE(X) ((X) != canOK)
"""
def CANSTATUS_FAILURE(status):
    return not CANSTATUS_SUCCESS(status)

"""
//
// Notification codes; appears in the notification WM__CANLIB message.
//
#define canEVENT_RX             32000       // Receive event
#define canEVENT_TX             32001       // Transmit event
#define canEVENT_ERROR          32002       // Error event
#define canEVENT_STATUS         32003       // Change-of-status event
#define canEVENT_ENVVAR         32004       // Change-of- envvar
"""
canEVENT_RX = 32000
canEVENT_TX = 32001
canEVENT_ERROR = 32002
canEVENT_STATUS = 32003
canEVENT_ENVVAR = 32004

"""
//
// These are used in the call to canSetNotify().
//
#define canNOTIFY_NONE          0           // Turn notifications off.
#define canNOTIFY_RX            0x0001      // Notify on receive
#define canNOTIFY_TX            0x0002      // Notify on transmit
#define canNOTIFY_ERROR         0x0004      // Notify on error
#define canNOTIFY_STATUS        0x0008      // Notify on (some) status changes
#define canNOTIFY_ENVVAR        0x0010      // Notify on Envvar change
"""
canNOTIFY_NONE = 0
canNOTIFY_RX = 0x0001
canNOTIFY_TX = 0x0002
canNOTIFY_ERROR = 0x0004
canNOTIFY_STATUS = 0x0008
canNOTIFY_ENVVAR = 0x0010

"""
//
// Circuit status flags.
//
#define canSTAT_ERROR_PASSIVE   0x00000001  // The circuit is error passive
#define canSTAT_BUS_OFF         0x00000002  // The circuit is Off Bus
#define canSTAT_ERROR_WARNING   0x00000004  // At least one error counter > 96
#define canSTAT_ERROR_ACTIVE    0x00000008  // The circuit is error active.
#define canSTAT_TX_PENDING      0x00000010  // There are messages pending transmission
#define canSTAT_RX_PENDING      0x00000020  // There are messages in the receive buffer
#define canSTAT_RESERVED_1      0x00000040
#define canSTAT_TXERR           0x00000080  // There has been at least one TX error
#define canSTAT_RXERR           0x00000100  // There has been at least one RX error of some sort
#define canSTAT_HW_OVERRUN      0x00000200  // The has been at least one HW buffer overflow
#define canSTAT_SW_OVERRUN      0x00000400  // The has been at least one SW buffer overflow
//
// For convenience.
#define canSTAT_OVERRUN         (canSTAT_HW_OVERRUN | canSTAT_SW_OVERRUN)
"""
canSTAT_ERROR_PASSIVE = 0x00000001
canSTAT_BUS_OFF = 0x00000002
canSTAT_ERROR_WARNING = 0x00000004
canSTAT_ERROR_ACTIVE = 0x00000008
canSTAT_TX_PENDING = 0x00000010
canSTAT_RX_PENDING = 0x00000020
canSTAT_RESERVED_1 = 0x00000040
canSTAT_TXERR = 0x00000080
canSTAT_RXERR = 0x00000100
canSTAT_HW_OVERRUN = 0x00000200
canSTAT_SW_OVERRUN = 0x00000400
canSTAT_OVERRUN = (canSTAT_HW_OVERRUN|canSTAT_SW_OVERRUN)

"""
//
// Message information flags, < 0x100
// All flags and/or combinations of them are meaningful for received messages
// RTR,STD,EXT,WAKEUP,ERROR_FRAME are meaningful also for transmitted messages
//
#define canMSG_MASK             0x00ff      // Used to mask the non-info bits
#define canMSG_RTR              0x0001      // Message is a remote request
#define canMSG_STD              0x0002      // Message has a standard ID
#define canMSG_EXT              0x0004      // Message has an extended ID
#define canMSG_WAKEUP           0x0008      // Message to be sent / was received in wakeup mode
#define canMSG_NERR             0x0010      // NERR was active during the message
#define canMSG_ERROR_FRAME      0x0020      // Message is an error frame
#define canMSG_TXACK            0x0040      // Message is a TX ACK (msg is really sent)
#define canMSG_TXRQ             0x0080      // Message is a TX REQUEST (msg is transfered to the chip)
"""
canMSG_MASK = 0x00ff
canMSG_RTR = 0x0001
canMSG_STD = 0x0002
canMSG_EXT = 0x0004
canMSG_WAKEUP = 0x0008
canMSG_NERR = 0x0010
canMSG_ERROR_FRAME = 0x0020
canMSG_TXACK = 0x0040
canMSG_TXRQ = 0x0080

"""
//
// Message error flags, >= 0x0100
//
#define canMSGERR_MASK          0xff00      // Used to mask the non-error bits
// 0x0100 reserved
#define canMSGERR_HW_OVERRUN    0x0200      // HW buffer overrun
#define canMSGERR_SW_OVERRUN    0x0400      // SW buffer overrun
#define canMSGERR_STUFF         0x0800      // Stuff error
#define canMSGERR_FORM          0x1000      // Form error
#define canMSGERR_CRC           0x2000      // CRC error
#define canMSGERR_BIT0          0x4000      // Sent dom, read rec
#define canMSGERR_BIT1          0x8000      // Sent rec, read dom
"""
canMSGERR_MASK = 0xff00
canMSGERR_HW_OVERRUN = 0x0200
canMSGERR_SW_OVERRUN = 0x0400
canMSGERR_STUFF = 0x0800
canMSGERR_FORM = 0x1000
canMSGERR_CRC = 0x2000
canMSGERR_BIT0 = 0x4000
canMSGERR_BIT1 = 0x8000

"""
//
// Convenience values for the message error flags.
//
#define canMSGERR_OVERRUN       0x0600      // Any overrun condition.
#define canMSGERR_BIT           0xC000      // Any bit error.
#define canMSGERR_BUSERR        0xF800      // Any RX error
"""
canMSGERR_OVERRUN = 0x0600
canMSGERR_BIT = 0xC000
canMSGERR_BUSERR = 0xF800

"""
/*
** Transceiver line modes.
*/
#define canTRANSCEIVER_LINEMODE_NA          0  // Not Affected/Not available.
#define canTRANSCEIVER_LINEMODE_SWC_SLEEP   4  // SWC Sleep Mode.
#define canTRANSCEIVER_LINEMODE_SWC_NORMAL  5  // SWC Normal Mode.
#define canTRANSCEIVER_LINEMODE_SWC_FAST    6  // SWC High-Speed Mode.
#define canTRANSCEIVER_LINEMODE_SWC_WAKEUP  7  // SWC Wakeup Mode.
#define canTRANSCEIVER_LINEMODE_SLEEP       8  // Sleep mode for those supporting it.
#define canTRANSCEIVER_LINEMODE_NORMAL      9  // Normal mode (the inverse of sleep mode) for those supporting it.
#define canTRANSCEIVER_LINEMODE_STDBY      10  // Standby for those who support it
#define canTRANSCEIVER_LINEMODE_TT_CAN_H   11  // Truck & Trailer: operating mode single wire using CAN high
#define canTRANSCEIVER_LINEMODE_TT_CAN_L   12  // Truck & Trailer: operating mode single wire using CAN low
#define canTRANSCEIVER_LINEMODE_OEM1       13  // Reserved for OEM apps
#define canTRANSCEIVER_LINEMODE_OEM2       14  // Reserved for OEM apps
#define canTRANSCEIVER_LINEMODE_OEM3       15  // Reserved for OEM apps
#define canTRANSCEIVER_LINEMODE_OEM4       16  // Reserved for OEM apps

#define canTRANSCEIVER_RESNET_NA            0
#define canTRANSCEIVER_RESNET_MASTER        1
#define canTRANSCEIVER_RESNET_MASTER_STBY   2
#define canTRANSCEIVER_RESNET_SLAVE         3
"""
canTRANSCEIVER_LINEMODE_NA = 0
canTRANSCEIVER_LINEMODE_SWC_SLEEP = 4
canTRANSCEIVER_LINEMODE_SWC_NORMAL = 5
canTRANSCEIVER_LINEMODE_SWC_FAST = 6
canTRANSCEIVER_LINEMODE_SWC_WAKEUP = 7
canTRANSCEIVER_LINEMODE_SLEEP = 8
canTRANSCEIVER_LINEMODE_NORMAL = 9
canTRANSCEIVER_LINEMODE_STDBY = 10
canTRANSCEIVER_LINEMODE_TT_CAN_H = 11
canTRANSCEIVER_LINEMODE_TT_CAN_L = 12
canTRANSCEIVER_LINEMODE_OEM1 = 13
canTRANSCEIVER_LINEMODE_OEM2 = 14
canTRANSCEIVER_LINEMODE_OEM3 = 15
canTRANSCEIVER_LINEMODE_OEM4 = 16
canTRANSCEIVER_RESNET_NA = 0
canTRANSCEIVER_RESNET_MASTER = 1
canTRANSCEIVER_RESNET_MASTER_STBY = 2
canTRANSCEIVER_RESNET_SLAVE = 3

"""
/*
** Transceiver (logical) types. Also see src\include\hwnames.h and
** registered document 048.
*/
#define canTRANSCEIVER_TYPE_UNKNOWN         0
#define canTRANSCEIVER_TYPE_251             1
#define canTRANSCEIVER_TYPE_252             2
#define canTRANSCEIVER_TYPE_DNOPTO          3
#define canTRANSCEIVER_TYPE_W210            4
#define canTRANSCEIVER_TYPE_SWC_PROTO       5  // Prototype. 
#define canTRANSCEIVER_TYPE_SWC             6
#define canTRANSCEIVER_TYPE_EVA             7
#define canTRANSCEIVER_TYPE_FIBER           8
#define canTRANSCEIVER_TYPE_K251            9 // K-line + 82c251
#define canTRANSCEIVER_TYPE_K              10 // K-line, without CAN
#define canTRANSCEIVER_TYPE_1054_OPTO      11 // 1054 with optical isolation
#define canTRANSCEIVER_TYPE_SWC_OPTO       12 // SWC with optical isolation
#define canTRANSCEIVER_TYPE_TT             13 // B10011S truck-and-trailer
#define canTRANSCEIVER_TYPE_1050           14 // TJA1050
#define canTRANSCEIVER_TYPE_1050_OPTO      15 // TJA1050 with optical isolation
#define canTRANSCEIVER_TYPE_1041           16  // 1041
#define canTRANSCEIVER_TYPE_1041_OPTO      17  // 1041 with optical isolation
#define canTRANSCEIVER_TYPE_RS485          18  // RS485 (i.e. J1708)
#define canTRANSCEIVER_TYPE_LIN            19  // LIN
#define canTRANSCEIVER_TYPE_KONE           20  // KONE
#define canTRANSCEIVER_TYPE_LINX_LIN       64
#define canTRANSCEIVER_TYPE_LINX_J1708     66
#define canTRANSCEIVER_TYPE_LINX_K         68
#define canTRANSCEIVER_TYPE_LINX_SWC       70
#define canTRANSCEIVER_TYPE_LINX_LS        72
"""
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

"""
#endif
"""
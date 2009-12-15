"""
File: canstat.py

This file is the canstat.h file from the CANLIB SDK translated into Python
using the ctypes package.
"""

import ctypes


class c_canStatus(ctypes.c_int):
    """
    Class: c_canStatus
    
    Representation of CANLIB's canStatus type.
    
    Parent class: ctypes.c_int
    """
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
canERR__RESERVED = -33


canStatusLookupTable = {}
canStatusLookupTable[canOK] = "canOK"
canStatusLookupTable[canERR_PARAM] = "canERR_PARAM"
canStatusLookupTable[canERR_NOMSG] = "canERR_NOMSG"
canStatusLookupTable[canERR_NOTFOUND] = "canERR_NOTFOUND"
canStatusLookupTable[canERR_NOMEM] = "canERR_NOMEM"
canStatusLookupTable[canERR_NOCHANNELS] = "canERR_NOCHANNELS"
canStatusLookupTable[canERR_RESERVED_3] = "canERR_NOCHANNELS"
canStatusLookupTable[canERR_TIMEOUT] = "canERR_TIMEOUT"
canStatusLookupTable[canERR_NOTINITIALIZED] = "canERR_NOTINITIALIZED"
canStatusLookupTable[canERR_NOHANDLES] = "canERR_NOHANDLES"
canStatusLookupTable[canERR_INVHANDLE] = "canERR_INVHANDLE"
canStatusLookupTable[canERR_INIFILE] = "canERR_INIFILE"
canStatusLookupTable[canERR_DRIVER] = "canERR_DRIVER"
canStatusLookupTable[canERR_TXBUFOFL] = "canERR_TXBUFOFL"
canStatusLookupTable[canERR_RESERVED_1] = "canERR_RESERVED_1"
canStatusLookupTable[canERR_HARDWARE] = "canERR_HARDWARE"
canStatusLookupTable[canERR_DYNALOAD] = "canERR_DYNALOAD"
canStatusLookupTable[canERR_DYNALIB] = "canERR_DYNALIB"
canStatusLookupTable[canERR_DYNAINIT] = "canERR_DYNAINIT"
canStatusLookupTable[canERR_NOT_SUPPORTED] = "canERR_NOT_SUPPORTED"
canStatusLookupTable[canERR_RESERVED_5] = "canERR_RESERVED_5"
canStatusLookupTable[canERR_RESERVED_6] = "canERR_RESERVED_6"
canStatusLookupTable[canERR_RESERVED_2] = "canERR_RESERVED_2"
canStatusLookupTable[canERR_DRIVERLOAD] = "canERR_DRIVERLOAD"
canStatusLookupTable[canERR_DRIVERFAILED] = "canERR_DRIVERFAILED"
canStatusLookupTable[canERR_NOCONFIGMGR] = "canERR_NOCONFIGMGR"
canStatusLookupTable[canERR_NOCARD] = "canERR_NOCARD"
canStatusLookupTable[canERR_RESERVED_7] = "canERR_RESERVED_7"
canStatusLookupTable[canERR_REGISTRY] = "canERR_REGISTRY"
canStatusLookupTable[canERR_LICENSE] = "canERR_LICENSE"
canStatusLookupTable[canERR_INTERNAL] = "canERR_INTERNAL"
canStatusLookupTable[canERR_NO_ACCESS] = "canERR_NO_ACCESS"
canStatusLookupTable[canERR_NOT_IMPLEMENTED] = "canERR_NOT_IMPLEMENTED"
canStatusLookupTable[canERR__RESERVED] = "canERR__RESERVED"


def CANSTATUS_SUCCESS(status):
    """
    Method: CANSTATUS_SUCCESS
    
    Determines if a given status value indicates a successful operation or
    not.
    
    Parameters:
        status: the status value to be checked
    
    Returns:
        True if the status value indicates a successful operation, False if it
        does not.
    """
    return (status >= canOK)

canEVENT_RX = 32000
canEVENT_TX = 32001
canEVENT_ERROR = 32002
canEVENT_STATUS = 32003
canEVENT_ENVVAR = 32004

canNOTIFY_NONE = 0
canNOTIFY_RX = 0x0001
canNOTIFY_TX = 0x0002
canNOTIFY_ERROR = 0x0004
canNOTIFY_STATUS = 0x0008
canNOTIFY_ENVVAR = 0x0010

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
canSTAT_OVERRUN = (canSTAT_HW_OVERRUN | canSTAT_SW_OVERRUN)

canMSG_MASK = 0x00ff
canMSG_RTR = 0x0001
canMSG_STD = 0x0002
canMSG_EXT = 0x0004
canMSG_WAKEUP = 0x0008
canMSG_NERR = 0x0010
canMSG_ERROR_FRAME = 0x0020
canMSG_TXACK = 0x0040
canMSG_TXRQ = 0x0080

canMSGERR_MASK = 0xff00
canMSGERR_HW_OVERRUN = 0x0200
canMSGERR_SW_OVERRUN = 0x0400
canMSGERR_STUFF = 0x0800
canMSGERR_FORM = 0x1000
canMSGERR_CRC = 0x2000
canMSGERR_BIT0 = 0x4000
canMSGERR_BIT1 = 0x8000

canMSGERR_OVERRUN = 0x0600
canMSGERR_BIT = 0xC000
canMSGERR_BUSERR = 0xF800

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

canTransceiverTypeStrings = {}

canTransceiverTypeStrings[canTRANSCEIVER_TYPE_UNKNOWN] = "Unknown/undefined"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_251] = "82C251"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_252] = "82C252/TJA1053/TJA1054"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_DNOPTO] = "Optoisolated 82C251"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_W210] = \
  "canTRANSCEIVER_TYPE_W210"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_SWC_PROTO] = "AU5790 prototype"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_SWC] = "AU5790"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_EVA] = "canTRANSCEIVER_TYPE_EVA"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_FIBER] = \
  "82C251 with fibre extension"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_K251] = \
  "canTRANSCEIVER_TYPE_K251"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_K] = "canTRANSCEIVER_TYPE_K"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_1054_OPTO] = \
  "TJA1054 optical isolation"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_SWC_OPTO] = \
  "AU5790 optical isolation"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_TT] = \
  "B10011S Truck-And-Trailer"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_1050] = "TJA1050"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_1050_OPTO] = \
  "TJA1050 optical isolation"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_1041] = "TJA1041"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_1041_OPTO] = \
  "TJA1041 optical isolation"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_RS485] = \
  "canTRANSCEIVER_TYPE_RS485"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LIN] = "LIN"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_KONE] = \
  "canTRANSCEIVER_TYPE_KONE"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LINX_LIN] = \
  "canTRANSCEIVER_TYPE_LINX_LIN"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LINX_J1708] = \
  "canTRANSCEIVER_TYPE_LINX_J170"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LINX_K] = \
  "canTRANSCEIVER_TYPE_LINX_K"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LINX_SWC] = \
  "canTRANSCEIVER_TYPE_LINX_SWC"
canTransceiverTypeStrings[canTRANSCEIVER_TYPE_LINX_LS] = \
  "canTRANSCEIVER_TYPE_LINX_LS"

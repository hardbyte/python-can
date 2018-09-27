# coding: utf-8

"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

import ctypes

class LUID(ctypes.Structure):
    _fields_ = [
        ("LowPart", ctypes.c_uint32),
        ("HighPart", ctypes.c_int32),
    ]
PLUID = ctypes.POINTER(LUID)


class VCIID(ctypes.Union):
    _fields_ = [
        ("AsLuid", LUID),
        ("AsInt64", ctypes.c_int64),
    ]
PVCIID = ctypes.POINTER(VCIID)


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_char * 8),
    ]


class VCIDEVICEINFO(ctypes.Structure):
    class UniqueHardwareId(ctypes.Union):
        _fields_ = [
            ("AsChar", ctypes.c_char * 16),
            ("AsGuid", GUID),
        ]
    _fields_ = [
        ("VciObjectId", VCIID),
        ("DeviceClass", GUID),
        ("DriverMajorVersion", ctypes.c_uint8),
        ("DriverMinorVersion", ctypes.c_uint8),
        ("DriverBuildVersion", ctypes.c_uint16),
        ("HardwareBranchVersion", ctypes.c_uint8),
        ("HardwareMajorVersion", ctypes.c_uint8),
        ("HardwareMinorVersion", ctypes.c_uint8),
        ("HardwareBuildVersion", ctypes.c_uint8),
        ("UniqueHardwareId", UniqueHardwareId),
        ("Description", ctypes.c_char * 128),
        ("Manufacturer", ctypes.c_char * 126),
        ("DriverReleaseVersion", ctypes.c_uint16),
    ]

    def __str__(self):
        return "Mfg: {}, Dev: {} HW: {}.{}.{}.{} Drv: {}.{}.{}.{}".format(
            self.Manufacturer,
            self.Description,
            self.HardwareBranchVersion,
            self.HardwareMajorVersion,
            self.HardwareMinorVersion,
            self.HardwareBuildVersion,
            self.DriverReleaseVersion,
            self.DriverMajorVersion,
            self.DriverMinorVersion,
            self.DriverBuildVersion
        )
PVCIDEVICEINFO = ctypes.POINTER(VCIDEVICEINFO)


class CANLINESTATUS(ctypes.Structure):
    _fields_ = [
        ("bOpMode", ctypes.c_uint8),
        ("bBtReg0", ctypes.c_uint8),
        ("bBtReg1", ctypes.c_uint8),
        ("bBusLoad", ctypes.c_uint8),
        ("dwStatus", ctypes.c_uint32)
    ]
PCANLINESTATUS = ctypes.POINTER(CANLINESTATUS)


class CANCHANSTATUS(ctypes.Structure):
    _fields_ = [
        ("sLineStatus", CANLINESTATUS),
        ("fActivated", ctypes.c_uint32),
        ("fRxOverrun", ctypes.c_uint32),
        ("bRxFifoLoad", ctypes.c_uint8),
        ("bTxFifoLoad", ctypes.c_uint8)
    ]
PCANCHANSTATUS = ctypes.POINTER(CANCHANSTATUS)


class CANCAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("wCtrlType", ctypes.c_uint16),
        ("wBusCoupling", ctypes.c_uint16),
        ("dwFeatures", ctypes.c_uint32),
        ("dwClockFreq", ctypes.c_uint32),
        ("dwTscDivisor", ctypes.c_uint32),
        ("dwCmsDivisor", ctypes.c_uint32),
        ("dwCmsMaxTicks", ctypes.c_uint32),
        ("dwDtxDivisor", ctypes.c_uint32),
        ("dwDtxMaxTicks", ctypes.c_uint32)
    ]
PCANCAPABILITIES = ctypes.POINTER(CANCAPABILITIES)


class CANMSGINFO(ctypes.Union):
    class Bytes(ctypes.Structure):
        _fields_ = [
            ("bType", ctypes.c_uint8),
            ("bAddFlags", ctypes.c_uint8),
            ("bFlags", ctypes.c_uint8),
            ("bAccept", ctypes.c_uint8),
        ]

    class Bits(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_uint32, 8),
            ("ssm", ctypes.c_uint32, 1),
            ("hi", ctypes.c_uint32, 2),
            ("res", ctypes.c_uint32, 5),
            ("dlc", ctypes.c_uint32, 4),
            ("ovr", ctypes.c_uint32, 1),
            ("srr", ctypes.c_uint32, 1),
            ("rtr", ctypes.c_uint32, 1),
            ("ext", ctypes.c_uint32, 1),
            ("afc", ctypes.c_uint32, 8)
        ]

    _fields_ = [
        ("Bytes", Bytes),
        ("Bits", Bits)
    ]
PCANMSGINFO = ctypes.POINTER(CANMSGINFO)


class CANMSG(ctypes.Structure):
    _fields_ = [
        ("dwTime", ctypes.c_uint32),
        ("dwMsgId", ctypes.c_uint32),
        ("uMsgInfo", CANMSGINFO),
        ("abData", ctypes.c_uint8 * 8)
    ]
PCANMSG = ctypes.POINTER(CANMSG)

class CANCYCLICTXMSG(ctypes.Structure):
    _fields_ = [
        ("wCycleTime", ctypes.c_uint16),
        ("bIncrMode", ctypes.c_uint8),
        ("bByteIndex", ctypes.c_uint8),
        ("dwMsgId", ctypes.c_uint32),
        ("uMsgInfo", CANMSGINFO),
        ("abData", ctypes.c_uint8 * 8)
    ]
PCANCYCLICTXMSG = ctypes.POINTER(CANCYCLICTXMSG)

"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V4 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

import ctypes


class LUID(ctypes.Structure):
    _fields_ = [("LowPart", ctypes.c_uint32), ("HighPart", ctypes.c_int32)]


PLUID = ctypes.POINTER(LUID)


class VCIID(ctypes.Union):
    _fields_ = [("AsLuid", LUID), ("AsInt64", ctypes.c_int64)]


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
        _fields_ = [("AsChar", ctypes.c_char * 16), ("AsGuid", GUID)]

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
            self.DriverBuildVersion,
        )


PVCIDEVICEINFO = ctypes.POINTER(VCIDEVICEINFO)


class CANMSGINFO(ctypes.Union):
    class Bytes(ctypes.Structure):
        _fields_ = [
            ("bType", ctypes.c_uint8),  # type (see CAN_MSGTYPE_ constants)
            (
                "bAddFlags",
                ctypes.c_uint8,
            ),  # extended flags (see CAN_MSGFLAGS2_ constants). AKA bFlags2 in VCI v4
            ("bFlags", ctypes.c_uint8),  # flags (see CAN_MSGFLAGS_ constants)
            ("bAccept", ctypes.c_uint8),  # accept code (see CAN_ACCEPT_ constants)
        ]

    class Bits(ctypes.Structure):
        _fields_ = [
            ("type", ctypes.c_uint32, 8),  # type (see CAN_MSGTYPE_ constants)
            ("ssm", ctypes.c_uint32, 1),  # single shot mode
            ("hpm", ctypes.c_uint32, 1),  # high priority message
            ("edl", ctypes.c_uint32, 1),  # extended data length
            ("fdr", ctypes.c_uint32, 1),  # fast data bit rate
            ("esi", ctypes.c_uint32, 1),  # error state indicator
            ("res", ctypes.c_uint32, 3),  # reserved set to 0
            ("dlc", ctypes.c_uint32, 4),  # data length code
            ("ovr", ctypes.c_uint32, 1),  # data overrun
            ("srr", ctypes.c_uint32, 1),  # self reception request
            ("rtr", ctypes.c_uint32, 1),  # remote transmission request
            (
                "ext",
                ctypes.c_uint32,
                1,
            ),  # extended frame format (0=standard, 1=extended)
            ("afc", ctypes.c_uint32, 8),  # accept code (see CAN_ACCEPT_ constants)
        ]

    _fields_ = [("Bytes", Bytes), ("Bits", Bits)]


PCANMSGINFO = ctypes.POINTER(CANMSGINFO)


class CANCYCLICTXMSG(ctypes.Structure):
    _fields_ = [
        ("wCycleTime", ctypes.c_uint16),
        ("bIncrMode", ctypes.c_uint8),
        ("bByteIndex", ctypes.c_uint8),
        ("dwMsgId", ctypes.c_uint32),
        ("uMsgInfo", CANMSGINFO),
        ("abData", ctypes.c_uint8 * 8),
    ]


PCANCYCLICTXMSG = ctypes.POINTER(CANCYCLICTXMSG)


class CANBTP(ctypes.Structure):
    _fields_ = [
        ("dwMode", ctypes.c_uint32),  # timing mode (see CAN_BTMODE_ const)
        ("dwBPS", ctypes.c_uint32),  # bits per second or prescaler (see CAN_BTMODE_RAW)
        ("wTS1", ctypes.c_uint16),  # length of time segment 1 in quanta
        ("wTS2", ctypes.c_uint16),  # length of time segment 2 in quanta
        ("wSJW", ctypes.c_uint16),  # re-synchronization jump width im quanta
        (
            "wTDO",
            ctypes.c_uint16,
        ),  # transceiver delay offset (SSP offset) in quanta (0 = disabled, 0xFFFF = simplified SSP positioning)
    ]

    def __str__(self):
        return "dwMode=%d, dwBPS=%d, wTS1=%d,  wTS2=%d, wSJW=%d, wTDO=%d" % (
            self.dwMode,
            self.dwBPS,
            self.wTS1,
            self.wTS2,
            self.wSJW,
            self.wTDO,
        )


PCANBTP = ctypes.POINTER(CANBTP)


class CANCAPABILITIES2(ctypes.Structure):
    _fields_ = [
        ("wCtrlType", ctypes.c_uint16),  # Type of CAN controller (see CAN_CTRL_ const)
        ("wBusCoupling", ctypes.c_uint16),  # Type of Bus coupling (see CAN_BUSC_ const)
        (
            "dwFeatures",
            ctypes.c_uint32,
        ),  # supported features (see CAN_FEATURE_ constants)
        ("dwCanClkFreq", ctypes.c_uint32),  # CAN clock frequency [Hz]
        ("sSdrRangeMin", CANBTP),  # minimum bit timing values for standard bit rate
        ("sSdrRangeMax", CANBTP),  # maximum bit timing values for standard bit rate
        ("sFdrRangeMin", CANBTP),  # minimum bit timing values for fast data bit rate
        ("sFdrRangeMax", CANBTP),  # maximum bit timing values for fast data bit rate
        (
            "dwTscClkFreq",
            ctypes.c_uint32,
        ),  # clock frequency of the time stamp counter [Hz]
        ("dwTscDivisor", ctypes.c_uint32),  # divisor for the message time stamp counter
        (
            "dwCmsClkFreq",
            ctypes.c_uint32,
        ),  # clock frequency of cyclic message scheduler [Hz]
        ("dwCmsDivisor", ctypes.c_uint32),  # divisor for the cyclic message scheduler
        (
            "dwCmsMaxTicks",
            ctypes.c_uint32,
        ),  # maximum tick count value of the cyclic message
        (
            "dwDtxClkFreq",
            ctypes.c_uint32,
        ),  # clock frequency of the delayed message transmitter [Hz]
        (
            "dwDtxDivisor",
            ctypes.c_uint32,
        ),  # divisor for the delayed message transmitter
        (
            "dwDtxMaxTicks",
            ctypes.c_uint32,
        ),  # maximum tick count value of the delayed message transmitter
    ]

    def __str__(self):
        cap = ", ".join(
            (
                "wCtrlType=%s" % self.wCtrlType,
                "wBusCoupling=%s" % self.wBusCoupling,
                "dwFeatures=%s" % self.dwFeatures,
                "dwCanClkFreq=%s" % self.dwCanClkFreq,
                "sSdrRangeMin=%s" % self.sSdrRangeMin,
                "sSdrRangeMax=%s" % self.sSdrRangeMax,
                "sFdrRangeMin=%s" % self.sFdrRangeMin,
                "sFdrRangeMax=%s" % self.sFdrRangeMax,
                "dwTscClkFreq=%s" % self.dwTscClkFreq,
                "dwTscDivisor=%s" % self.dwTscDivisor,
                "dwCmsClkFreq=%s" % self.dwCmsClkFreq,
                "dwCmsDivisor=%s" % self.dwCmsDivisor,
                "dwCmsMaxTicks=%s" % self.dwCmsMaxTicks,
                "dwDtxClkFreq=%s" % self.dwDtxClkFreq,
                "dwDtxDivisor=%s" % self.dwDtxDivisor,
                "dwDtxMaxTicks=%s" % self.dwDtxMaxTicks,
            )
        )
        return cap


PCANCAPABILITIES2 = ctypes.POINTER(CANCAPABILITIES2)


class CANLINESTATUS2(ctypes.Structure):
    _fields_ = [
        ("bOpMode", ctypes.c_uint8),  # current CAN operating mode
        ("bExMode", ctypes.c_uint8),  # current CAN extended operating mode
        ("bBusLoad", ctypes.c_uint8),  # average bus load in percent (0..100)
        ("bReserved", ctypes.c_uint8),  # reserved set to 0
        ("sBtpSdr", CANBTP),  # standard bit rate timing
        ("sBtpFdr", CANBTP),  # fast data bit rate timing
        ("dwStatus", ctypes.c_uint32),  # status of the CAN controller (see CAN_STATUS_)
    ]

    def __str__(self) -> str:
        return "\n".join(
            (
                f"Std Operating Mode:  {self.bOpMode}",
                f"Ext Operating Mode:  {self.bExMode}",
                f"Bus Load (%):  {self.bBusLoad}",
                f"Standard Bitrate Timing:  {self.sBtpSdr}",
                f"Fast Datarate timing:  {self.sBtpFdr}",
                f"CAN Controller Status:  {self.dwStatus}",
            )
        )


PCANLINESTATUS2 = ctypes.POINTER(CANLINESTATUS2)


class CANCHANSTATUS2(ctypes.Structure):
    _fields_ = [
        ("sLineStatus", CANLINESTATUS2),  # current CAN line status
        ("fActivated", ctypes.c_uint8),  # TRUE if the channel is activated
        ("fRxOverrun", ctypes.c_uint8),  # TRUE if receive FIFO overrun occurred
        ("bRxFifoLoad", ctypes.c_uint8),  # receive FIFO load in percent (0..100)
        ("bTxFifoLoad", ctypes.c_uint8),  # transmit FIFO load in percent (0..100)
    ]

    def __str__(self) -> str:
        return "\n".join(
            (
                f"Status:  {self.sLineStatus}",
                f"Activated:  {bool(self.fActivated)}",
                f"RxOverrun:  {bool(self.fRxOverrun)}",
                f"Rx Buffer Load (%):  {self.bRxFifoLoad}",
                f"Tx Buffer Load (%):  {self.bTxFifoLoad}",
            )
        )


PCANCHANSTATUS2 = ctypes.POINTER(CANCHANSTATUS2)


class CANMSG2(ctypes.Structure):
    _fields_ = [
        ("dwTime", ctypes.c_uint32),  # time stamp for receive message
        ("rsvd", ctypes.c_uint32),  # reserved (set to 0)
        ("dwMsgId", ctypes.c_uint32),  # CAN message identifier (INTEL format)
        ("uMsgInfo", CANMSGINFO),  # message information (bit field)
        ("abData", ctypes.c_uint8 * 64),  # message data
    ]

    def __str__(self) -> str:
        return """ID: 0x{:04x}{} DLC: {:02d} DATA: {}""".format(
            self.dwMsgId,
            "[RTR]" if self.uMsgInfo.Bits.rtr else "",
            self.uMsgInfo.Bits.dlc,
            memoryview(self.abData)[: self.uMsgInfo.Bits.dlc].hex(sep=" "),
        )


PCANMSG2 = ctypes.POINTER(CANMSG2)


class CANCYCLICTXMSG2(ctypes.Structure):
    _fields_ = [
        ("wCycleTime", ctypes.c_uint16),  # cycle time for the message in ticks
        (
            "bIncrMode",
            ctypes.c_uint8,
        ),  # auto increment mode (see CAN_CTXMSG_INC_ const)
        (
            "bByteIndex",
            ctypes.c_uint8,
        ),  # index of the byte within abData[] to increment
        ("dwMsgId", ctypes.c_uint32),  # message identifier (INTEL format)
        ("uMsgInfo", CANMSGINFO),  # message information (bit field)
        ("abData", ctypes.c_uint8 * 64),  # message data
    ]


PCANCYCLICTXMSG2 = ctypes.POINTER(CANCYCLICTXMSG2)

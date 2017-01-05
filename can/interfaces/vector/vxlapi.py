# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems
Authors: Julien Grave <grave.jul@gmail.com>
"""
# Import Standard Python Modules
# ==============================
import ctypes
import logging
import platform
import sys

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Vector XL API Definitions
# =========================
# Load Windows DLL
if sys.platform == 'win32':
    _xlapi_dll = None
    architecture = platform.architecture()[0]
    try:
        if architecture == '64bit':
            _xlapi_dll = ctypes.windll.LoadLibrary('vxlapi64')
        else:
            _xlapi_dll = ctypes.windll.LoadLibrary('vxlapi')
    except OSError:
        if architecture == '64bit':
            LOG.error('Cannot load Dynamic XL Driver Library (vxlapi64.dll)')
        else:
            LOG.error('Cannot load Dynamic XL Driver Library (vxlapi.dll)')
else:
    LOG.error('This library is only availabe for Windows')
    exit(1)

# Bus types
XL_BUS_TYPE_NONE = 0x00000000
XL_BUS_TYPE_CAN = 0x00000001
XL_BUS_TYPE_LIN = 0x00000002
XL_BUS_TYPE_FLEXRAY = 0x00000004
XL_BUS_TYPE_AFDX = 0x00000008  # former BUS_TYPE_BEAN
XL_BUS_TYPE_MOST = 0x00000010
XL_BUS_TYPE_DAIO = 0x00000040  # IO cab/piggy
XL_BUS_TYPE_J1708 = 0x00000100
XL_BUS_TYPE_ETHERNET = 0x00001000
XL_BUS_TYPE_A429 = 0x00002000

# Transceiver types
# =================
# CAN Cab
XL_TRANSCEIVER_TYPE_NONE = 0x0000
XL_TRANSCEIVER_TYPE_CAN_251 = 0x0001
XL_TRANSCEIVER_TYPE_CAN_252 = 0x0002
XL_TRANSCEIVER_TYPE_CAN_DNOPTO = 0x0003
XL_TRANSCEIVER_TYPE_CAN_SWC_PROTO = 0x0005  # Prototype. Driver may latch-up.
XL_TRANSCEIVER_TYPE_CAN_SWC = 0x0006
XL_TRANSCEIVER_TYPE_CAN_EVA = 0x0007
XL_TRANSCEIVER_TYPE_CAN_FIBER = 0x0008
XL_TRANSCEIVER_TYPE_CAN_1054_OPTO = 0x000B  # 1054 with optical isolation
XL_TRANSCEIVER_TYPE_CAN_SWC_OPTO = 0x000C  # SWC with optical isolation
XL_TRANSCEIVER_TYPE_CAN_B10011S = 0x000D  # B10011S truck-and-trailer
XL_TRANSCEIVER_TYPE_CAN_1050 = 0x000E  # 1050
XL_TRANSCEIVER_TYPE_CAN_1050_OPTO = 0x000F  # 1050 with optical isolation
XL_TRANSCEIVER_TYPE_CAN_1041 = 0x0010  # 1041
XL_TRANSCEIVER_TYPE_CAN_1041_OPTO = 0x0011  # 1041 with optical isolation
XL_TRANSCEIVER_TYPE_CAN_VIRTUAL = 0x0016  # Virtual CAN Transceiver for Virtual CAN Bus Driver
XL_TRANSCEIVER_TYPE_LIN_6258_OPTO = 0x0017  # Vector LINcab 6258opto with transceiver Infineon TLE6258
XL_TRANSCEIVER_TYPE_LIN_6259_OPTO = 0x0019  # Vector LINcab 6259opto with transceiver Infineon TLE6259
XL_TRANSCEIVER_TYPE_DAIO_8444_OPTO = 0x001D  # Vector IOcab 8444  (8 dig.Inp.; 4 dig.Outp.; 4 ana.Inp.; 4 ana.Outp.)
XL_TRANSCEIVER_TYPE_CAN_1041A_OPTO = 0x0021  # 1041A with optical isolation
XL_TRANSCEIVER_TYPE_LIN_6259_MAG = 0x0023  # LIN transceiver 6259, with transceiver Infineon TLE6259, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_LIN_7259_MAG = 0x0025  # LIN transceiver 7259, with transceiver Infineon TLE7259, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_LIN_7269_MAG = 0x0027  # LIN transceiver 7269, with transceiver Infineon TLE7269, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_CAN_1054_MAG = 0x0033  # TJA1054, magnetically isolated, with selectable termination resistor (via 4th IO line)
XL_TRANSCEIVER_TYPE_CAN_251_MAG = 0x0035  # 82C250/251 or equivalent, magnetically isolated
XL_TRANSCEIVER_TYPE_CAN_1050_MAG = 0x0037  # TJA1050, magnetically isolated
XL_TRANSCEIVER_TYPE_CAN_1040_MAG = 0x0039  # TJA1040, magnetically isolated
XL_TRANSCEIVER_TYPE_CAN_1041A_MAG = 0x003B  # TJA1041A, magnetically isolated
XL_TRANSCEIVER_TYPE_TWIN_CAN_1041A_MAG = 0x0080  # TWINcab with two TJA1041, magnetically isolated
XL_TRANSCEIVER_TYPE_TWIN_LIN_7269_MAG = 0x0081  # TWINcab with two 7259, Infineon TLE7259, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_TWIN_CAN_1041AV2_MAG = 0x0082  # TWINcab with two TJA1041, magnetically isolated
XL_TRANSCEIVER_TYPE_TWIN_CAN_1054_1041A_MAG = 0x0083  # TWINcab with TJA1054A and TJA1041A with magnetic isolation

# CAN PiggyBack
XL_TRANSCEIVER_TYPE_PB_CAN_251 = 0x0101
XL_TRANSCEIVER_TYPE_PB_CAN_1054 = 0x0103
XL_TRANSCEIVER_TYPE_PB_CAN_251_OPTO = 0x0105
XL_TRANSCEIVER_TYPE_PB_CAN_SWC = 0x010B
# 0x010D not supported, 0x010F, 0x0111, 0x0113 reserved for future use!!
XL_TRANSCEIVER_TYPE_PB_CAN_1054_OPTO = 0x0115
XL_TRANSCEIVER_TYPE_PB_CAN_SWC_OPTO = 0x0117
XL_TRANSCEIVER_TYPE_PB_CAN_TT_OPTO = 0x0119
XL_TRANSCEIVER_TYPE_PB_CAN_1050 = 0x011B
XL_TRANSCEIVER_TYPE_PB_CAN_1050_OPTO = 0x011D
XL_TRANSCEIVER_TYPE_PB_CAN_1041 = 0x011F
XL_TRANSCEIVER_TYPE_PB_CAN_1041_OPTO = 0x0121
XL_TRANSCEIVER_TYPE_PB_LIN_6258_OPTO = 0x0129  # LIN piggy back with transceiver Infineon TLE6258
XL_TRANSCEIVER_TYPE_PB_LIN_6259_OPTO = 0x012B  # LIN piggy back with transceiver Infineon TLE6259
XL_TRANSCEIVER_TYPE_PB_LIN_6259_MAG = 0x012D  # LIN piggy back with transceiver Infineon TLE6259, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_PB_CAN_1041A_OPTO = 0x012F  # CAN transceiver 1041A
XL_TRANSCEIVER_TYPE_PB_LIN_7259_MAG = 0x0131  # LIN piggy back with transceiver Infineon TLE7259, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_PB_LIN_7269_MAG = 0x0133  # LIN piggy back with transceiver Infineon TLE7269, magnetically isolated, stress functionality
XL_TRANSCEIVER_TYPE_PB_CAN_251_MAG = 0x0135  # 82C250/251 or compatible, magnetically isolated
XL_TRANSCEIVER_TYPE_PB_CAN_1050_MAG = 0x0136  # TJA 1050, magnetically isolated
XL_TRANSCEIVER_TYPE_PB_CAN_1040_MAG = 0x0137  # TJA 1040, magnetically isolated
XL_TRANSCEIVER_TYPE_PB_CAN_1041A_MAG = 0x0138  # TJA 1041A, magnetically isolated
XL_TRANSCEIVER_TYPE_PB_DAIO_8444_OPTO = 0x0139  # optically isolated IO piggy
XL_TRANSCEIVER_TYPE_PB_CAN_1054_MAG = 0x013B  # TJA1054, magnetically isolated, with selectable termination resistor (via 4th IO line)
XL_TRANSCEIVER_TYPE_CAN_1051_CAP_FIX = 0x013C  # TJA1051 - fixed transceiver on e.g. 16xx/8970
XL_TRANSCEIVER_TYPE_DAIO_1021_FIX = 0x013D  # Onboard IO of VN1630/VN1640
XL_TRANSCEIVER_TYPE_LIN_7269_CAP_FIX = 0x013E  # TLE7269 - fixed transceiver on 1611
XL_TRANSCEIVER_TYPE_PB_CAN_1051_CAP = 0x013F  # TJA 1051, capacitive isolated
XL_TRANSCEIVER_TYPE_PB_CAN_SWC_7356_CAP = 0x0140  # Single Wire NCV7356, capacitive isolated
XL_TRANSCEIVER_TYPE_PB_CAN_1055_CAP = 0x0141  # TJA1055, capacitive isolated, with selectable termination resistor (via 4th IO line)
XL_TRANSCEIVER_TYPE_PB_CAN_1057_CAP = 0x0142  # TJA 1057, capacitive isolated
XL_TRANSCEIVER_TYPE_A429_HOLT8596_FIX = 0x0143  # Onboard HOLT 8596 TX transceiver on VN0601
XL_TRANSCEIVER_TYPE_A429_HOLT8455_FIX = 0x0144  # Onboard HOLT 8455 RX transceiver on VN0601

# FlexRay PiggyBacks
XL_TRANSCEIVER_TYPE_PB_FR_1080 = 0x0201  # TJA 1080
XL_TRANSCEIVER_TYPE_PB_FR_1080_MAG = 0x0202  # TJA 1080 magnetically isolated piggy
XL_TRANSCEIVER_TYPE_PB_FR_1080A_MAG = 0x0203  # TJA 1080A magnetically isolated piggy
XL_TRANSCEIVER_TYPE_PB_FR_1082_CAP = 0x0204  # TJA 1082 capacitive isolated piggy
XL_TRANSCEIVER_TYPE_PB_FRC_1082_CAP = 0x0205  # TJA 1082 capacitive isolated piggy with CANpiggy form factor
XL_TRANSCEIVER_TYPE_FR_1082_CAP_FIX = 0x0206  # TJA 1082 capacitive isolated piggy fixed transceiver - e.g. 7610

XL_TRANSCEIVER_TYPE_MOST150_ONBOARD = 0x0220  # Onboard MOST150 transceiver of VN2640

# Ethernet Phys
XL_TRANSCEIVER_TYPE_ETH_BCM54810_FIX = 0x0230  # Onboard Broadcom Ethernet PHY on VN5610 and VX0312
XL_TRANSCEIVER_TYPE_ETH_AR8031_FIX = 0x0231  # Onboard Atheros Ethernet PHY
XL_TRANSCEIVER_TYPE_ETH_BCM89810_FIX = 0x0232  # Onboard Broadcom Ethernet PHY
XL_TRANSCEIVER_TYPE_ETH_TJA1100_FIX = 0x0233  # Onboard NXP Ethernet PHY
XL_TRANSCEIVER_TYPE_ETH_BCM54810_89811_FIX = 0x0234  # Onboard Broadcom Ethernet PHYs (e.g. VN5610A - BCM54810: RJ45, BCM89811: DSUB)

# IOpiggy 8642
XL_TRANSCEIVER_TYPE_PB_DAIO_8642 = 0x0280  # Iopiggy for VN8900
XL_TRANSCEIVER_TYPE_DAIO_AL_ONLY = 0x028f  # virtual piggy type for activation line only (e.g. VN8810ini)
XL_TRANSCEIVER_TYPE_DAIO_1021_FIX_WITH_AL = 0x0290  # On board IO with Activation Line (e.g. VN5640)
XL_TRANSCEIVER_TYPE_DAIO_AL_WU = 0x0291  # virtual piggy type for activation line and WakeUp Line only (e.g. VN5610A)

# Transceiver Operation Modes
# ===========================
XL_TRANSCEIVER_LINEMODE_TWO_LINE = (ctypes.c_uint(0x0001))
XL_TRANSCEIVER_LINEMODE_NA = (ctypes.c_uint(0x0000))
XL_TRANSCEIVER_LINEMODE_CAN_H = (ctypes.c_uint(0x0002))
XL_TRANSCEIVER_LINEMODE_CAN_L = (ctypes.c_uint(0x0003))
XL_TRANSCEIVER_LINEMODE_SWC_SLEEP = (ctypes.c_uint(0x0004))  # SWC Sleep Mode
XL_TRANSCEIVER_LINEMODE_SWC_NORMAL = (ctypes.c_uint(0x0005))  # SWC Normal Mode
XL_TRANSCEIVER_LINEMODE_SWC_FAST = (ctypes.c_uint(0x0006))  # SWC High-Speed
XL_TRANSCEIVER_LINEMODE_SWC_WAKEUP = (ctypes.c_uint(0x0007))  # SWC Wakeup Mode
XL_TRANSCEIVER_LINEMODE_SLEEP = (ctypes.c_uint(0x0008))
XL_TRANSCEIVER_LINEMODE_NORMAL = (ctypes.c_uint(0x0009))
XL_TRANSCEIVER_LINEMODE_STDBY = (ctypes.c_uint(0x000a))
XL_TRANSCEIVER_LINEMODE_TT_CAN_H = (
    ctypes.c_uint(0x000b)
)  # truck & trailer: operating mode single wire using CAN high
XL_TRANSCEIVER_LINEMODE_TT_CAN_L = (
    ctypes.c_uint(0x000c)
)  # truck & trailer: operating mode single wire using CAN low
XL_TRANSCEIVER_LINEMODE_EVA_00 = (ctypes.c_uint(0x000d))  # CANcab Eva
XL_TRANSCEIVER_LINEMODE_EVA_01 = (ctypes.c_uint(0x000e))  # CANcab Eva
XL_TRANSCEIVER_LINEMODE_EVA_10 = (ctypes.c_uint(0x000f))  # CANcab Eva
XL_TRANSCEIVER_LINEMODE_EVA_11 = (ctypes.c_uint(0x0010))  # CANcab Eva

# Transceiver Status Flags
# ========================
# (not all used, but for compatibility reasons)
XL_TRANSCEIVER_STATUS_PRESENT = (ctypes.c_uint(0x0001))
XL_TRANSCEIVER_STATUS_POWER_GOOD = (ctypes.c_uint(0x0010))
XL_TRANSCEIVER_STATUS_EXT_POWER_GOOD = (ctypes.c_uint(0x0020))
XL_TRANSCEIVER_STATUS_NOT_SUPPORTED = (ctypes.c_uint(0x0040))

# =============================================================================
# driver status
XL_SUCCESS = 0  # =0x0000
XL_PENDING = 1  # =0x0001

XL_ERR_QUEUE_IS_EMPTY = 10  # =0x000A
XL_ERR_QUEUE_IS_FULL = 11  # =0x000B
XL_ERR_TX_NOT_POSSIBLE = 12  # =0x000C
XL_ERR_NO_LICENSE = 14  # =0x000E
XL_ERR_WRONG_PARAMETER = 101  # =0x0065
XL_ERR_TWICE_REGISTER = 110  # =0x006E
XL_ERR_INVALID_CHAN_INDEX = 111  # =0x006F
XL_ERR_INVALID_ACCESS = 112  # =0x0070
XL_ERR_PORT_IS_OFFLINE = 113  # =0x0071
XL_ERR_CHAN_IS_ONLINE = 116  # =0x0074
XL_ERR_NOT_IMPLEMENTED = 117  # =0x0075
XL_ERR_INVALID_PORT = 118  # =0x0076
XL_ERR_HW_NOT_READY = 120  # =0x0078
XL_ERR_CMD_TIMEOUT = 121  # =0x0079
XL_ERR_CMD_HANDLING = 122  # =0x007A
XL_ERR_HW_NOT_PRESENT = 129  # =0x0081
XL_ERR_NOTIFY_ALREADY_ACTIVE = 131  # =0x0083
XL_ERR_INVALID_TAG = 132  # =0x0084
XL_ERR_INVALID_RESERVED_FLD = 133  # =0x0085
XL_ERR_INVALID_SIZE = 134  # =0x0086
XL_ERR_INSUFFICIENT_BUFFER = 135  # =0x0087
XL_ERR_ERROR_CRC = 136  # =0x0088
XL_ERR_BAD_EXE_FORMAT = 137  # =0x0089
XL_ERR_NO_SYSTEM_RESOURCES = 138  # =0x008A
XL_ERR_NOT_FOUND = 139  # =0x008B
XL_ERR_INVALID_ADDRESS = 140  # =0x008C
XL_ERR_REQ_NOT_ACCEP = 141  # =0x008D
XL_ERR_INVALID_LEVEL = 142  # =0x008E
XL_ERR_NO_DATA_DETECTED = 143  # =0x008F
XL_ERR_INTERNAL_ERROR = 144  # =0x0090
XL_ERR_UNEXP_NET_ERR = 145  # =0x0091
XL_ERR_INVALID_USER_BUFFER = 146  # =0x0092
XL_ERR_NO_RESOURCES = 152  # =0x0098
XL_ERR_WRONG_CHIP_TYPE = 153  # =0x0099
XL_ERR_WRONG_COMMAND = 154  # =0x009A
XL_ERR_INVALID_HANDLE = 155  # =0x009B
XL_ERR_RESERVED_NOT_ZERO = 157  # =0x009D
XL_ERR_INIT_ACCESS_MISSING = 158  # =0x009E
XL_ERR_CANNOT_OPEN_DRIVER = 201  # =0x00C9
XL_ERR_WRONG_BUS_TYPE = 202  # =0x00CA
XL_ERR_DLL_NOT_FOUND = 203  # =0x00CB
XL_ERR_INVALID_CHANNEL_MASK = 204  # =0x00CC
XL_ERR_NOT_SUPPORTED = 205  # =0x00CD
# special stream defines
XL_ERR_CONNECTION_BROKEN = 210  # =0x00D2
XL_ERR_CONNECTION_CLOSED = 211  # =0x00D3
XL_ERR_INVALID_STREAM_NAME = 212  # =0x00D4
XL_ERR_CONNECTION_FAILED = 213  # =0x00D5
XL_ERR_STREAM_NOT_FOUND = 214  # =0x00D6
XL_ERR_STREAM_NOT_CONNECTED = 215  # =0x00D7
XL_ERR_QUEUE_OVERRUN = 216  # =0x00D8
XL_ERROR = 255  # =0x00FF

# =============================================================================
# common event tags
XL_RECEIVE_MSG = (ctypes.c_ushort(0x0001))
XL_CHIP_STATE = (ctypes.c_ushort(0x0004))
XL_TRANSCEIVER_INFO = (ctypes.c_ushort(0x0006))
XL_TRANSCEIVER = (XL_TRANSCEIVER_INFO)
XL_TIMER_EVENT = (ctypes.c_ushort(0x0008))
XL_TIMER = (XL_TIMER_EVENT)
XL_TRANSMIT_MSG = (ctypes.c_ushort(0x000A))
XL_SYNC_PULSE = (ctypes.c_ushort(0x000B))
XL_APPLICATION_NOTIFICATION = (ctypes.c_ushort(0x000F))

# CAN/CAN-FD event tags
# Rx
XL_CAN_EV_TAG_RX_OK = (ctypes.c_ushort(0x0400))
XL_CAN_EV_TAG_RX_ERROR = (ctypes.c_ushort(0x0401))
XL_CAN_EV_TAG_TX_ERROR = (ctypes.c_ushort(0x0402))
XL_CAN_EV_TAG_TX_REQUEST = (ctypes.c_ushort(0x0403))
XL_CAN_EV_TAG_TX_OK = (ctypes.c_ushort(0x0404))
XL_CAN_EV_TAG_CHIP_STATE = (ctypes.c_ushort(0x0409))

# CAN/CAN-FD event tags
# Tx
XL_CAN_EV_TAG_TX_MSG = (ctypes.c_ushort(0x0440))

XLuint64 = ctypes.c_ulonglong

# defines for XL_SYNC_PULSE_EV::triggerSource and s_xl_sync_pulse::pulseCode
XL_SYNC_PULSE_EXTERNAL = 0x00
XL_SYNC_PULSE_OUR = 0x01
XL_SYNC_PULSE_OUR_SHARED = 0x02


# definition of the sync pulse event for xl interface versions V3 and higher
# (XL_INTERFACE_VERSION_V3, XL_INTERFACE_VERSION_V4, ..)
class s_xl_sync_pulse_ev(ctypes.Structure):
    _fields_ = [('triggerSource', ctypes.c_uint), ('reserved', ctypes.c_uint),
                ('time', XLuint64)]


# definition of the sync pulse event for xl interface versions V1 and V2
# (XL_INTERFACE_VERSION_V1, XL_INTERFACE_VERSION_V2)
class s_xl_sync_pulse(ctypes.Structure):
    _fields_ = [('pulseCode', ctypes.c_ubyte), ('time', XLuint64)]


# defines for the supported hardware
XL_HWTYPE_NONE = 0
XL_HWTYPE_VIRTUAL = 1
XL_HWTYPE_CANCARDX = 2
XL_HWTYPE_CANAC2PCI = 6
XL_HWTYPE_CANCARDY = 12
XL_HWTYPE_CANCARDXL = 15
XL_HWTYPE_CANCASEXL = 21
XL_HWTYPE_CANCASEXL_LOG_OBSOLETE = 23
XL_HWTYPE_CANBOARDXL = 25  # CANboardXL, CANboardXL PCIe
XL_HWTYPE_CANBOARDXL_PXI = 27  # CANboardXL pxi
XL_HWTYPE_VN2600 = 29
XL_HWTYPE_VN2610 = XL_HWTYPE_VN2600
XL_HWTYPE_VN3300 = 37
XL_HWTYPE_VN3600 = 39
XL_HWTYPE_VN7600 = 41
XL_HWTYPE_CANCARDXLE = 43
XL_HWTYPE_VN8900 = 45
XL_HWTYPE_VN8950 = 47
XL_HWTYPE_VN2640 = 53
XL_HWTYPE_VN1610 = 55
XL_HWTYPE_VN1630 = 57
XL_HWTYPE_VN1640 = 59
XL_HWTYPE_VN8970 = 61
XL_HWTYPE_VN1611 = 63
XL_HWTYPE_VN5610 = 65
XL_HWTYPE_VN7570 = 67
XL_HWTYPE_IPCLIENT = 69
XL_HWTYPE_IPSERVER = 71
XL_HWTYPE_VX1121 = 73
XL_HWTYPE_VX1131 = 75
XL_HWTYPE_VT6204 = 77
XL_HWTYPE_VN1630_LOG = 79
XL_HWTYPE_VN7610 = 81
XL_HWTYPE_VN7572 = 83
XL_HWTYPE_VN8972 = 85
XL_HWTYPE_VN0601 = 87
XL_HWTYPE_VX0312 = 91
XL_HWTYPE_VN8800 = 95
XL_HWTYPE_IPCL8800 = 96
XL_HWTYPE_IPSRV8800 = 97
XL_HWTYPE_CSMCAN = 98
XL_HWTYPE_VN5610A = 101
XL_HWTYPE_VN7640 = 102

# =============================================================================
XLstringType = ctypes.c_char_p

# =============================================================================
# accessmask
XLaccess = XLuint64

# =============================================================================
# Defines
# =======
# message flags
MAX_MSG_LEN = 8

# interface version for our events
XL_INTERFACE_VERSION_V2 = 2
XL_INTERFACE_VERSION_V3 = 3
XL_INTERFACE_VERSION_V4 = 4

# current version
XL_INTERFACE_VERSION = XL_INTERFACE_VERSION_V3


# structure for XL_RECEIVE_MSG, XL_TRANSMIT_MSG
class s_xl_can_msg(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ulong), ('flags', ctypes.c_ushort),
                ('dlc', ctypes.c_ushort), ('res1', XLuint64),
                ('data', ctypes.c_ubyte * MAX_MSG_LEN), ('res2', XLuint64)]


# structure for XL_TRANSMIT_DAIO_DATA

# flags masks
XL_DAIO_DATA_GET = 0x8000
XL_DAIO_DATA_VALUE_DIGITAL = 0x0001
XL_DAIO_DATA_VALUE_ANALOG = 0x0002
XL_DAIO_DATA_PWM = 0x0010

# optional function flags
XL_DAIO_MODE_PULSE = 0x0020  # generates pulse in values of PWM


class s_xl_daio_data(ctypes.Structure):
    _fields_ = [
        ('flags', ctypes.c_ushort), ('timestamp_correction', ctypes.c_uint),
        ('mask_digital', ctypes.c_ubyte), ('value_digital', ctypes.c_ubyte),
        ('mask_analog', ctypes.c_ubyte), ('reserved0', ctypes.c_ubyte),
        ('value_analog', ctypes.c_ushort * 4),
        ('pwm_frequency', ctypes.c_uint), ('pwm_value', ctypes.c_ushort),
        ('reserved1', ctypes.c_uint), ('reserved2', ctypes.c_uint)
    ]


class s_xl_io_digital_data(ctypes.Structure):
    _fields_ = [('digitalInputData', ctypes.c_uint)]


class s_xl_io_analog_data(ctypes.Structure):
    _fields_ = [('measuredAnalogData0', ctypes.c_uint),
                ('measuredAnalogData1', ctypes.c_uint),
                ('measuredAnalogData2', ctypes.c_uint),
                ('measuredAnalogData3', ctypes.c_uint)]


class s_xl_daio_piggy_data_data(ctypes.Union):
    _fields_ = [('digital', s_xl_io_digital_data), ('analog',
                                                    s_xl_io_analog_data)]


class s_xl_daio_piggy_data(ctypes.Structure):
    _fields_ = [('daioEvtTag', ctypes.c_uint), ('triggerType', ctypes.c_uint),
                ('data', s_xl_daio_piggy_data_data)]


# structure for XL_CHIP_STATE
XL_CHIPSTAT_BUSOFF = 0x01
XL_CHIPSTAT_ERROR_PASSIVE = 0x02
XL_CHIPSTAT_ERROR_WARNING = 0x04
XL_CHIPSTAT_ERROR_ACTIVE = 0x08


class s_xl_chip_state(ctypes.Structure):
    _fields_ = [('busStatus', ctypes.c_ubyte),
                ('txErrorCounter', ctypes.c_ubyte),
                ('rxErrorCounter', ctypes.c_ubyte)]


# structure and defines for XL_TRANSCEIVER
XL_TRANSCEIVER_EVENT_NONE = 0
XL_TRANSCEIVER_EVENT_INSERTED = 1  # cable was inserted
XL_TRANSCEIVER_EVENT_REMOVED = 2  # cable was removed
XL_TRANSCEIVER_EVENT_STATE_CHANGE = 3  # transceiver state changed


class s_xl_transceiver(ctypes.Structure):
    _fields_ = [('event_reason', ctypes.c_ubyte), ('is_present',
                                                   ctypes.c_ubyte)]


# defines for SET_OUTPUT_MODE
XL_OUTPUT_MODE_SILENT = 0  # switch CAN trx into default silent mode
XL_OUTPUT_MODE_NORMAL = 1  # switch CAN trx into normal mode
XL_OUTPUT_MODE_TX_OFF = 2  # switch CAN trx into silent mode with tx pin off
XL_OUTPUT_MODE_SJA_1000_SILENT = 3  # switch CAN trx into SJA1000 silent mode

# Transceiver modes
XL_TRANSCEIVER_EVENT_ERROR = 1
XL_TRANSCEIVER_EVENT_CHANGED = 2


# =============================================================================
# LIN lib
# =======
# LIN event structures
class s_xl_lin_msg(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ubyte), ('dlc', ctypes.c_ubyte),
                ('flags', ctypes.c_ushort), ('data', ctypes.c_ubyte * 8),
                ('crc', ctypes.c_ubyte)]


class s_xl_lin_sleep(ctypes.Structure):
    _fields_ = [('flag', ctypes.c_ubyte)]


class s_xl_lin_no_ans(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ubyte)]


class s_xl_lin_wake_up(ctypes.Structure):
    _fields_ = [('flag', ctypes.c_ubyte), ('unused', ctypes.c_ubyte * 3),
                ('startOffs', ctypes.c_uint), ('width', ctypes.c_uint)]


class s_xl_lin_crc_info(ctypes.Structure):
    _fields_ = [('id', ctypes.c_ubyte), ('flags', ctypes.c_ubyte)]


# LIN messages structure
class s_xl_lin_msg_api(ctypes.Union):
    _fields_ = [('linMsg', s_xl_lin_msg), ('linNoAns', s_xl_lin_no_ans),
                ('linWakeUp', s_xl_lin_wake_up), ('linSleep', s_xl_lin_sleep),
                ('linCRCinfo', s_xl_lin_crc_info)]


# BASIC bus message structure
class s_xl_tag_data(ctypes.Union):
    _fields_ = [('msg', s_xl_can_msg), ('chipState', s_xl_chip_state),
                ('linMsgApi', s_xl_lin_msg_api),
                ('syncPulse', s_xl_sync_pulse), ('daioData', s_xl_daio_data),
                ('transceiver', s_xl_transceiver),
                ('daioPiggyData', s_xl_daio_piggy_data)]


XLeventTag = ctypes.c_ubyte


# XL_EVENT structures
# event type definition
class s_xl_event(ctypes.Structure):
    _fields_ = [('tag', XLeventTag), ('chanIndex', ctypes.c_ubyte),
                ('transId', ctypes.c_ushort), ('portHandle', ctypes.c_ushort),
                ('flags', ctypes.c_ubyte), ('reserved', ctypes.c_ubyte),
                ('timeStamp', XLuint64), ('tagData', s_xl_tag_data)]


XLevent = s_xl_event

# driver status
XLstatus = ctypes.c_short

# defines for xlGetDriverConfig structures
XL_MAX_LENGTH = 31
XL_CONFIG_MAX_CHANNELS = 64

# activate - channel flags
XL_ACTIVATE_NONE = 0
XL_ACTIVATE_RESET_CLOCK = 8


class XLbusParams_data_can(ctypes.Structure):
    _fields_ = [('bitRate', ctypes.c_uint), ('sjw', ctypes.c_ubyte),
                ('tseg1', ctypes.c_ubyte), ('tseg2', ctypes.c_ubyte),
                ('sam', ctypes.c_ubyte), ('outputMode', ctypes.c_ubyte),
                ('reserved', ctypes.c_ubyte * 7),
                ('canOpMode', ctypes.c_ubyte)]


class XLbusParams_data(ctypes.Union):
    _fields_ = [('can', XLbusParams_data_can)]


class XLbusParams(ctypes.Structure):
    _fields_ = [('busType', ctypes.c_uint), ('data', XLbusParams_data)]


# porthandle
XL_INVALID_PORTHANDLE = (-1)
XLportHandle = ctypes.c_long
pXLportHandle = ctypes.POINTER(XLportHandle)


# structures for xlGetDriverConfig
class s_xl_channel_config(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('name', ctypes.c_char * (XL_MAX_LENGTH + 1)),
        ('hwType', ctypes.c_ubyte), ('hwIndex', ctypes.c_ubyte),
        ('hwChannel', ctypes.c_ubyte), ('transceiverType', ctypes.c_ushort),
        ('transceiverState', ctypes.c_ushort),
        ('configError', ctypes.c_ushort), ('channelIndex', ctypes.c_ubyte),
        ('channelMask', XLuint64), ('channelCapabilities', ctypes.c_uint),
        ('channelBusCapabilities', ctypes.c_uint), ('isOnBus', ctypes.c_ubyte),
        ('connectedBusType', ctypes.c_uint), ('busParams', XLbusParams),
        ('_doNotUse', ctypes.c_uint), ('driverVersion', ctypes.c_uint),
        ('interfaceVersion', ctypes.c_uint), ('raw_data', ctypes.c_uint * 10),
        ('serialNumber', ctypes.c_uint), ('articleNumber', ctypes.c_uint),
        ('transceiverName', ctypes.c_char * (XL_MAX_LENGTH + 1)),
        ('specialCabFlags', ctypes.c_uint), ('dominantTimeout', ctypes.c_uint),
        ('dominantRecessiveDelay', ctypes.c_ubyte),
        ('recessiveDominantDelay', ctypes.c_ubyte), ('connectionInfo',
                                                     ctypes.c_ubyte),
        ('currentlyAvailableTimestamps', ctypes.c_ubyte), (
            'minimalSupplyVoltage', ctypes.c_ushort), (
                'maximalSupplyVoltage', ctypes.c_ushort), (
                    'maximalBaudrate', ctypes.c_uint), ('fpgaCoreCapabilities',
                                                        ctypes.c_ubyte),
        ('specialDeviceStatus',
         ctypes.c_ubyte), ('channelBusActiveCapabilities', ctypes.c_ushort), (
             'breakOffset', ctypes.c_ushort),
        ('delimiterOffset', ctypes.c_ushort), ('reserved', ctypes.c_uint * 3)
    ]


XLchannelConfig = s_xl_channel_config


class s_xl_driver_config(ctypes.Structure):
    _fields_ = [('dllVersion', ctypes.c_uint), ('channelCount', ctypes.c_uint),
                ('reserved', ctypes.c_uint * 10),
                ('channel', XLchannelConfig * XL_CONFIG_MAX_CHANNELS)]


XLdriverConfig = s_xl_driver_config

# =============================================================================
# Functions calls
# ===============

# xlOpenDriver();
xlOpenDriver = _xlapi_dll.xlOpenDriver
xlOpenDriver.argtypes = []
xlOpenDriver.restype = XLstatus


def open_driver():
    xl_status = XLstatus(xlOpenDriver())
    return xl_status


# xlCloseDriver();
xlCloseDriver = _xlapi_dll.xlCloseDriver
xlCloseDriver.argtypes = []
xlCloseDriver.restype = XLstatus


def close_driver():
    xl_status = XLstatus(xlCloseDriver())
    return xl_status


# xlGetApplConfig();
xlGetApplConfig = _xlapi_dll.xlGetApplConfig
xlGetApplConfig.argtypes = [
    ctypes.c_char_p, ctypes.c_uint, ctypes.POINTER(ctypes.c_uint),
    ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(ctypes.c_uint), ctypes.c_uint
]
xlGetApplConfig.restype = XLstatus


def get_appl_config(app_name=ctypes.c_char_p('xlCANcontrol'),
                    app_channel=ctypes.c_uint(0),
                    hw_type=ctypes.c_uint(0),
                    hw_index=ctypes.c_uint(0),
                    hw_channel=ctypes.c_uint(0),
                    bus_type=ctypes.c_uint(XL_BUS_TYPE_CAN)):
    xl_status = XLstatus(
        xlGetApplConfig(app_name, app_channel,
                        ctypes.byref(hw_type),
                        ctypes.byref(hw_index),
                        ctypes.byref(hw_channel), bus_type))
    return xl_status


# xlSetApplConfig();
xlSetApplConfig = _xlapi_dll.xlSetApplConfig
xlSetApplConfig.argtypes = [
    ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint,
    ctypes.c_uint, ctypes.c_uint
]
xlSetApplConfig.restype = XLstatus


def set_appl_config(app_name, app_channel, hw_type, hw_index, hw_channel,
                    bus_type):
    xl_status = XLstatus(
        xlSetApplConfig(app_name, app_channel, hw_type, hw_index, hw_channel,
                        bus_type))
    return xl_status


# xlGetDriverConfig();
xlGetDriverConfig = _xlapi_dll.xlGetDriverConfig
xlGetDriverConfig.argtypes = [ctypes.POINTER(XLdriverConfig)]
xlGetDriverConfig.restype = XLstatus


def get_driver_config(driver_config):
    xl_status = XLstatus(xlGetDriverConfig(ctypes.byref(driver_config)))
    return xl_status


# xlGetChannelIndex();
xlGetChannelIndex = _xlapi_dll.xlGetChannelIndex
xlGetChannelIndex.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelIndex.restype = ctypes.c_int


def get_channel_index(hw_type=ctypes.c_int(XL_HWTYPE_CANCASEXL),
                      hw_index=ctypes.c_int(0),
                      hw_channel=ctypes.c_int(0)):
    hw_type = ctypes.c_int(hw_type)
    hw_index = ctypes.c_int(hw_index)
    hw_channel = ctypes.c_int(hw_channel)
    channel_index = ctypes.c_int(
        xlGetChannelIndex(hw_type, hw_index, hw_channel))
    return channel_index


# xlGetChannelMask();
xlGetChannelMask = _xlapi_dll.xlGetChannelMask
xlGetChannelMask.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
xlGetChannelMask.restype = XLaccess


def get_channel_mask(hw_type=ctypes.c_int(XL_HWTYPE_CANCASEXL),
                     hw_index=ctypes.c_int(0),
                     hw_channel=ctypes.c_int(0)):
    channel_mask = XLaccess(xlGetChannelMask(hw_type, hw_index, hw_channel))
    return channel_mask


# xlOpenPort();
xlOpenPort = _xlapi_dll.xlOpenPort
xlOpenPort.argtypes = [
    ctypes.POINTER(XLportHandle), ctypes.c_char_p, XLaccess,
    ctypes.POINTER(XLaccess), ctypes.c_uint, ctypes.c_uint, ctypes.c_uint
]
xlOpenPort.restype = XLstatus


def open_port(port_handle,
              access_mask,
              permission_mask,
              user_name=ctypes.c_char_p('xlCANcontrol'),
              rx_queue_size=ctypes.c_uint(256),
              xl_interface_version=ctypes.c_uint(XL_INTERFACE_VERSION),
              bus_type=ctypes.c_uint(XL_BUS_TYPE_CAN)):
    xl_status = XLstatus(
        xlOpenPort(
            ctypes.byref(port_handle), user_name, access_mask,
            ctypes.byref(permission_mask), rx_queue_size, xl_interface_version,
            bus_type))
    return xl_status


# xlClosePort();
xlClosePort = _xlapi_dll.xlClosePort
xlClosePort.argtypes = [XLportHandle]
xlClosePort.restype = XLstatus


def close_port(port_handle):
    xl_status = XLstatus(xlClosePort(port_handle))
    return xl_status


# xlActivateChannel();
xlActivateChannel = _xlapi_dll.xlActivateChannel
xlActivateChannel.argtypes = [
    XLportHandle, XLaccess, ctypes.c_uint, ctypes.c_uint
]
xlActivateChannel.restype = XLstatus


def activate_channel(port_handle,
                     access_mask,
                     bus_type=ctypes.c_uint(XL_BUS_TYPE_CAN),
                     flags=ctypes.c_uint(XL_ACTIVATE_RESET_CLOCK)):
    xl_status = XLstatus(
        xlActivateChannel(port_handle, access_mask, bus_type, flags))
    return xl_status


# xlDeactivateChannel();
xlDeactivateChannel = _xlapi_dll.xlDeactivateChannel
xlDeactivateChannel.argtypes = [XLportHandle, XLaccess]
xlDeactivateChannel.restype = XLstatus


def deactivate_channel(port_handle, access_mask):
    xl_status = XLstatus(xlDeactivateChannel(port_handle, access_mask))
    return xl_status


# xlReceive();
xlReceive = _xlapi_dll.xlReceive
xlReceive.argtypes = [
    XLportHandle, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLevent)
]
xlReceive.restype = XLstatus


def receive(port_handle, event_count, event_list):
    xl_status = XLstatus(
        xlReceive(port_handle,
                  ctypes.byref(event_count), ctypes.byref(event_list)))
    return xl_status


# xlGetEventString();
xlGetEventString = _xlapi_dll.xlGetEventString
xlGetEventString.argtypes = [ctypes.POINTER(XLevent)]
xlGetEventString.restype = XLstringType


def get_event_string(ev):
    string = XLstringType(xlGetEventString(ctypes.byref(ev)))
    return string


# xlGetErrorString();
xlGetErrorString = _xlapi_dll.xlGetErrorString
xlGetErrorString.argtypes = [XLstatus]
xlGetErrorString.restype = ctypes.c_char_p


def get_error_string(err):
    string = ctypes.c_char_p(xlGetErrorString(err))
    return string


# xlCanSetChannelBitrate();
xlCanSetChannelBitrate = _xlapi_dll.xlCanSetChannelBitrate
xlCanSetChannelBitrate.argtypes = [XLportHandle, XLaccess, ctypes.c_ulong]
xlCanSetChannelBitrate.restype = XLstatus


def can_set_channel_bitrate(port_handle, access_mask, bitrate):
    xl_status = XLstatus(
        xlCanSetChannelBitrate(port_handle, access_mask, bitrate))
    return xl_status


# xlCanTransmit();
xlCanTransmit = _xlapi_dll.xlCanTransmit
xlCanTransmit.argtypes = [
    XLportHandle, XLaccess, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p
]
xlCanTransmit.restype = XLstatus


def can_transmit(port_handle, access_mask, message_count, messages):
    xl_status = XLstatus(
        xlCanTransmit(port_handle, access_mask,
                      ctypes.byref(message_count), ctypes.byref(messages)))
    return xl_status

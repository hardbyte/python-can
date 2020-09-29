# coding: utf-8
"""Interface to use ETAS CAN USB modules (ES58X) with python-can.
Version: 1.0.0

Authors: Philipp Ahrendt
         Vincent Mailhol <mailhol.vincent@wanadoo.fr>

Language: Python 3.5 or greater

Copyright (C) 2020 ETAS K.K., Yokohama, Japan
http://www.etas.com

To use this interface you first need to install ETAS BOA.
You can download it at https://www.etas.com/en/downloadcenter/18102.php

Changelog:
    09/29/2020 - Version 1.0.0
        - First public release.
"""

## Deactivate pylint invalid-name (C0103). Rationale: the structures and attributes names taken from
## the C headers of the BOA API are kept untouched to simplify cross researches.
# pylint: disable=invalid-name

## Deactivate pylint too-few-public-methods (R0903). Rationale: all the classes which inherit from
## ctypes throw this warning.
# pylint: disable=too-few-public-methods

import logging
import sys
import os
import ctypes as ct
import aenum

import can

# Set up logging
FORMAT_HEADER = '%(asctime)s [%(levelname)s] '
global_logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(FORMAT_HEADER + '%(message)s'))
global_logger.addHandler(handler)

if sys.platform == "win32":
    if sys.maxsize > 2**32:  #Python 64 bits
        BOA_dll_path = os.path.join(os.getenv('PROGRAMFILES'),
                                    r'ETAS\BOA_V2\Bin\x64\Dll\Framework')
    else:  #Python 32 bits
        BOA_dll_path = os.path.join(os.getenv('PROGRAMFILES'),
                                    r'ETAS\BOA_V2\Bin\Win32\Dll\Framework')
    if os.path.exists(BOA_dll_path):
        try:  # Python 3.8's DLL handling
            os.add_dll_directory(BOA_dll_path)
        except AttributeError:  # Until Python 3.7, use PATH
            os.environ['PATH'] += os.pathsep + BOA_dll_path
    try:
        dll_ocd_proxy = ct.cdll.LoadLibrary("dll-ocdProxy.dll")
        dll_csi_bind = ct.cdll.LoadLibrary("dll-csiBind.dll")
    except OSError as error:
        dll_ocd_proxy = None
        global_logger.error("Failed to load Etas BOA dll: %s", error)
        if not os.path.exists(BOA_dll_path):
            global_logger.error("Default directory for BOA DLL (%s) does not exist. "
                                "Is BOA installed?", BOA_dll_path)
            global_logger.error("If BOA DLL are not installed in the default directory, "
                                "add it to your Windows Environment Path variable")
else:
    global_logger.warning("Etas interface is only available on Windows systems")


#///////////////////////////////////////////////////////////
# Basic type definitions
#///////////////////////////////////////////////////////////

OCI_ErrorCode = ct.c_uint32
OCI_URIName = ct.c_char_p
OCI_ControllerHandle = ct.c_int32
OCI_CANMessageDataType = ct.c_uint8
OCI_Time = ct.c_int64
OCI_QueueHandle = ct.c_int32
CSI_NodeType = ct.c_int32

CanData = ct.c_uint8 * 8
CanDataFD = ct.c_uint8 * 64

#///////////////////////////////////////////////////////////
# Constant value definitions
#///////////////////////////////////////////////////////////

# Special OCI_ControllerHandle value to indicate a missing or invalid handle.
OCI_NO_HANDLE = -1

OCI_ERR_FLAG_WARNING = 0x40000000
OCI_ERR_FLAG_ERROR = 0x80000000

OCI_ERR_TYPE = {
    0x00000000: {
        'name': 'OCI_ERR_TYPE_RESERVED',
        'description': 'Unspecified failure (reserved error code). Might be a software bug.'
    },
    0x00001000: {
        'name': 'OCI_ERR_TYPE_PARAM',
        'description': 'Parameter validation failed.'
    },
    0x00002000: {
        'name': 'OCI_ERR_TYPE_BIND',
        'description': 'Binding process of the API failed (probably an internal error.'
    },
    0x00003000: {
        'name': 'OCI_ERR_TYPE_SEMANTIC',
        'description': 'Failed to validate some preconditions.'
    },
    0x00004000: {
        'name': 'OCI_ERR_TYPE_RESOURCE',
        'description': 'Ran out of resources.',
    },
    0x00005000: {
        'name': 'OCI_ERR_TYPE_COMMUNICATION',
        'description': 'Communication problems with the hardware occurred.'
    },
    0x00006000: {
        'name': 'OCI_ERR_TYPE_INTERNAL',
        'description': 'Internal implementation error.'
    },
    0x0000F000: {
        'name': 'OCI_ERR_TYPE_PRIVATE',
        'description': r'Reserved for internal use. You should not see this message ¯\_(ツ)_/¯'
    }
}
OCI_ERR_TYPE_MASK = 0x0000F000

OCI_ERR_CODE = {
    0x00000000: {
        'name': 'OCI_SUCCESS',
        'description': 'OK: command successfully returned'
    },
    0x40004000: {
        'name': 'OCI_WARN_PARAM_ADAPTED',
        'description': 'Supplied parameters can not be used as is, proceed by adapting them in a '
                       'compatible manner.'
    },
    0x80001000: {
        'name': 'OCI_ERR_INVALID_PARAMETER',
        'description': 'One of the supplied parameters is incorrect. Can not proceed.'
    },
    0x80001001: {
        'name': 'OCI_ERR_INCONSISTENT_PARAMETER_SET',
        'description': 'Provided settings are implausible.'
    },
    0x80002000: {
        'name': 'OCI_ERR_PROTOCOL_VERSION_NOT_SUPPORTED',
        'description': 'Requested BOA API version is not supported.'
    },
    0x80002004: {
        'name': 'OCI_ERR_NO_INTERFACE',
        'description': 'Requested BOA API version is not supported.'
    },
    0x80002005: {
        'name': 'OCI_ERR_HW_NOT_PRESENT',
        'description': 'The requested hardware is not present.'
    },
    0x80003001: {
        'name': 'OCI_ERR_NO_CONFIG',
        'description': 'Controller could not be found. Is it connected?'
    },
    0x80005000: {
        'name': 'OCI_ERR_DRIVER_NO_RESPONSE',
        'description': 'Controller gave no response. Is it still connected?'
    },
    0x80005001: {
        'name': 'OCI_ERR_DRIVER_DISCONNECTED',
        'description': 'Controller was shutdown or disconnected.'
    },
    0x80006006: {
        'name': 'OCI_ERR_NOT_IMPLEMENTED',
        'description': 'Bug: the requested function is not implemented.'
    }
}
# Some direct aliases of above error codes for quick access
OCI_ERR_TYPE_RESERVED = 0x00000000
OCI_SUCCESS = 0x00000000
OCI_WARN_PARAM_ADAPTED = 0x40004000
OCI_ERR_INCONSISTENT_PARAMETER_SET = 0x80001001
OCI_ERR_PROTOCOL_VERSION_NOT_SUPPORTED = 0x80002000
OCI_ERR_NO_INTERFACE = 0x80002004
OCI_ERR_NO_CONFIG = 0x80003001

OCI_ERROR_STRING_LENGTH = 256

OCI_EVENT_DESTINATION_INBAND = 0x01
OCI_EVENT_DESTINATION_CALLBACK = 0x02
OCI_EVENT_DESTINATION_ALL = OCI_EVENT_DESTINATION_INBAND | OCI_EVENT_DESTINATION_CALLBACK

# samplesPerBit values
OCI_CAN_ONE_SAMPLE_PER_BIT = 1
OCI_CAN_THREE_SAMPLES_PER_BIT = 2

# busParticipationMode values
OCI_BUSMODE_PASSIVE = 1
OCI_BUSMODE_ACTIVE = 2

# syncEdge values
OCI_CAN_SINGLE_SYNC_EDGE = 1
OCI_CAN_DUAL_SYNC_EDGE = 2
OCI_CAN_EDGE_FILTER_DURING_BUS_INTEGRATION = 4

# physicalMedia values
OCI_CAN_MEDIA_HIGH_SPEED = 1
OCI_CAN_MEDIA_FAULT_TOLERANT = 2

# selfReceptionMode values
OCI_SELF_RECEPTION_OFF = 0
OCI_SELF_RECEPTION_ON = 1

# mode values
OCI_CONTROLLER_MODE_RUNNING = 0
OCI_CONTROLLER_MODE_SUSPENDED = 1

# CAN message flags
OCI_CAN_MSG_FLAG = {
    'extended': {
        'name': 'OCI_CAN_MSG_FLAG_EXTENDED',
        'value': 1,
        'description': 'Extended Frame Format (EFF)'
    },
    'remote_frame': {
        'name': 'OCI_CAN_MSG_FLAG_REMOTE_FRAME',
        'value': 2,
        'description': 'Remote Transmission Request frames (RTR)'
    },
    'selfreception': {
        'name': 'OCI_CAN_MSG_FLAG_SELFRECEPTION',
        'value': 4,
        'description': 'Message loopback (self reception)'
    },
    'bitrate_switch': {
        'name': 'OCI_CAN_MSG_FLAG_FD_DATA_BIT_RATE',
        'value': 8,
        'description': 'Bit Rate Switch (BRS: the second bitrate for payload data)'
    },
    'fd_trunc_and_pad': {
        'name': 'OCI_CAN_MSG_FLAG_FD_TRUNC_AND_PAD',
        'value': 16,
        'description': 'Truncate the data to the supported length and pad it'
    },
    'error_state_indicator': {
        'name': 'OCI_CAN_MSG_FLAG_FD_ERROR_PASSIVE',
        'value': 32,
        'description': 'Error State Indicator frames (ESI)'
    },
    'fd': {
        'name': 'OCI_CAN_MSG_FLAG_FD_DATA',
        'value': 64,
        'description': 'CAN-FD frames'
    },
}

OCI_CANFDSUPPORT = 1

OCI_NO_TIME = ct.c_int64(-1)

# OCI_CANRxMode
OCI_CAN_RXMODE_CAN_FRAMES_IGNORED = 1
OCI_CAN_RXMODE_CAN_FRAMES_USING_CAN_MESSAGE = 2

# OCI_CANFDRxMod
OCI_CANFDRXMODE_CANFD_FRAMES_IGNORED = 1
OCI_CANFDRXMODE_CANFD_FRAMES_USING_CAN_MESSAGE = 2
OCI_CANFDRXMODE_CANFD_FRAMES_USING_CANFD_MESSAGE = 4
OCI_CANFDRXMODE_CANFD_FRAMES_USING_CANFD_MESSAGE_PADDING = 8

# OCI_CANFDTxConfig
OCI_CANFDTX_USE_CAN_FRAMES_ONLY = 1
OCI_CANFDTX_USE_CANFD_FRAMES_ONLY = 2
OCI_CANFDTX_USE_CAN_AND_CANFD_FRAMES = 4

# OCI_CANMessageDataType
OCI_CAN_RX_MESSAGE = OCI_CANMessageDataType(1)
OCI_CAN_TX_MESSAGE = OCI_CANMessageDataType(2)
OCI_CAN_ERROR_FRAME = OCI_CANMessageDataType(3)
OCI_CAN_BUS_EVENT = OCI_CANMessageDataType(4)
OCI_CAN_INTERNAL_ERROR_EVENT = OCI_CANMessageDataType(5)
OCI_CAN_QUEUE_EVENT = OCI_CANMessageDataType(6)
OCI_CAN_TIMER_EVENT = OCI_CANMessageDataType(7)
OCI_CANFDRX_MESSAGE = OCI_CANMessageDataType(8)
OCI_CANFDTX_MESSAGE = OCI_CANMessageDataType(9)

CSI_NODE_MIN = CSI_NodeType(0)
CSI_NODE_MAX = CSI_NodeType(0x7fff)


#///////////////////////////////////////////////////////////
# ct.Structures definitions
#///////////////////////////////////////////////////////////

class BOA_API_Version(ct.Structure):
    """
    This parameter corresponds to the type *BOA_Version* in the C API, it was renamed to
    *BOA_API_Version* to avoid confusion with the software release versions.
    """
    _fields_ = [("majorVersion", ct.c_uint8),
                ("minorVersion", ct.c_uint8),
                ("bugfix", ct.c_uint8),
                ("build", ct.c_uint8)]

    def __iter__(self):
        for field_name, _field_type in self._fields_:
            yield getattr(self, field_name)

    def __str__(self):
        return '.'.join(str(i) for i in self)

    def __eq__(self, other):
        return tuple(self) == tuple(other)

    def __lt__(self, other):
        return tuple(self) < tuple(other)

    def __le__(self, other):
        return tuple(self) <= tuple(other)

    def __gt__(self, other):
        return tuple(self) > tuple(other)

    def __ge__(self, other):
        return tuple(self) >= tuple(other)

    def copy(self):
        """
        :rtype: can.interfaces.etas.BOA_API_Version
        :return: A new cloned instance.
        """
        res = BOA_API_Version()
        ct.pointer(res)[0] = self  # Force the copy
        return res

    def decrement(self):
        """
        Decrement the minorVersion number of the API. If the minorVersion is zero, carry on to the
        majorVersion number.

        :raise can.interfaces.etas.EtasError:
            If the minimum API version has been reached.
        """
        if self.minorVersion <= 0:
            if self < BOA_API_Version(1, 0, 0, 0):
                raise EtasError("Reached the minimum BOA API Version.")
            self.majorVersion -= 1
            self.minorVersion = HIGHEST_POSSIBLE_BOA_API_MINOR_VERSION
        else:
            self.minorVersion -= 1

# Below lines should be adjusted accordingly if a new BOA API version gets published.
LATEST_BOA_API = BOA_API_Version(1, 4, 0, 0)  # Latest BOA API as of 09/2020
HIGHEST_POSSIBLE_BOA_API_MINOR_VERSION = 4


class CSI_NodeRange(ct.Structure):
    """
    A range of nodes
    """
    _fields_ = [("min", CSI_NodeType),
                ("max", CSI_NodeType)]


class CSI_SubItem(ct.Structure):
    """
    Elements of the CSI tree
    """
    _fields_ = [("server", ct.c_uint8 * 172),
                ("nodeType", CSI_NodeType),
                ("uri_name", ct.c_char * 128),
                ("visibleName", ct.c_char * 4),
                ("version", BOA_API_Version),
                ("reserved2", ct.c_char * 88),
                ("serverAffinity", ct.c_uint8 * 16),
                ("requiredAffinity0", ct.c_uint8 * 16),
                ("reserved", ct.c_int32 * 4),
                ("requiredAffinity1", ct.c_uint8 * 16),
                ("count", ct.c_uint32),
                ("requiredAPI", ct.c_uint8 * 160)]


# Deactivate pylint unnecessary-pass (W0107) and protected-access (W0212). Rationale: below
# technique is the state of the art to implement recursive structures with ctype. Reference:
# https://stackoverflow.com/questions/1228158/python-ctype-recursive-structures
class CSI_Tree(ct.Structure):
    """
    Represents the CSI_Tree structure (tree representation of the connected hardware)
    """
    pass  # pylint: disable=unnecessary-pass

CSI_Tree._fields_ = [  # pylint: disable=protected-access
    ("item", CSI_SubItem),
    ("sibling", ct.POINTER(CSI_Tree)),
    ("child", ct.POINTER(CSI_Tree)),
    ("childrenProbed", ct.c_int)
]


class BusState(aenum.Enum):
    """
    The state in which a :class:`can.BusABC` can be.

    Overwriting :class:`can.BusState` in order to add the BUS_OFF and the STOPPED states (also,
    using names closer to the ISO 11898-1).
    """

    ERROR_ACTIVE = aenum.auto()
    """Active state: both TR and RX error count are strictly less than 96."""

    ERROR_WARNING = aenum.auto()
    """Warning state: either TX or RX error count is greater or equal to 96 (but both remain
       strictly below 128)."""

    ERROR_PASSIVE = aenum.auto()
    """Passive state: either TX or RX error count is greater or equal to 127 (but both remain
       strictly below 256)."""

    BUS_OFF = aenum.auto()
    """Bus off: either TX or RX error count is greater or equal to 256."""

    STOPPED = aenum.auto()
    """Device is stopped"""
can.BusState = BusState

OCI_CAN_BUS_EVENTS = {
    0x00000001: {
        'name': 'OCI_CAN_BUS_EVENT_STATE_ACTIVE',
        'description': 'Active state: both TR and RX error count are less than 96',
        'BusState': BusState.ERROR_ACTIVE
    },
    0x00000002: {
        'name': 'OCI_CAN_BUS_EVENT_STATE_PASSIVE',
        'description': 'Passive state: either TX or RX error count is greater than 127',
        'BusState': BusState.ERROR_PASSIVE
    },
    0x00000004: {
        'name': 'OCI_CAN_BUS_EVENT_STATE_ERRLIMIT',
        'description': 'Warning state: either TX or RX error count is greater than 96',
        'BusState': BusState.ERROR_WARNING
    },
    0x00000008: {
        'name': 'OCI_CAN_BUS_EVENT_STATE_BUSOFF',
        'description': 'Bus off',
        'BusState': BusState.BUS_OFF
    },
    0x00000010: {
        'name': 'OCI_CAN_BUS_EVENT_FAULT_TOLERANT_SINGLE_WIRE',
        'description': 'Lost connection on either CAN high or CAN low',
        'BusState': None
    },
    0x00000020: {
        'name': 'OCI_CAN_BUS_EVENT_PROTOCOL_EXCEPTION',
        'description': 'Protocol exception',
        'BusState': None
    },
}

OCI_CAN_BUS_EVENT_ALL = 0x0
for oci_can_bus_event in OCI_CAN_BUS_EVENTS:
    OCI_CAN_BUS_EVENT_ALL |= oci_can_bus_event

OCI_CAN_ERR_TYPES = {
    0x00000002: {
        "name": 'OCI_CAN_ERR_TYPE_FORMAT',
        "description": 'Frame format error'
    },
    0x00000004: {
        "name": 'OCI_CAN_ERR_TYPE_ACK',
        "description": 'Received no ACK on transmission'
    },
    0x00000008: {
        "name": 'OCI_CAN_ERR_TYPE_BIT',
        "description": 'Single bit error'
    },
    0x00000010: {
        "name": 'OCI_CAN_ERR_TYPE_CRC',
        "description": 'Incorrect CRC15'
    },
    0x00000020: {
        "name": 'OCI_CAN_ERR_TYPE_BIT_RECSV_BUT_DOMINANT',
        "description": 'Unable to send recessive bit: tried to send recessive bit 1 but monitored '
                       'dominant bit 0'
    },
    0x00000040: {
        "name": 'OCI_CAN_ERR_TYPE_BIT_DOMINANT_BUT_RECSV',
        "description": 'Unable to send dominant bit: tried to send dominant bit 0 but monitored '
                       'recessive bit 1'
    },
    0x00000080: {
        "name": 'OCI_CAN_ERR_TYPE_OVERLOAD',
        "description": 'Bus overload'
    },
    0x80000000: {
        "name": 'OCI_CAN_ERR_TYPE_OTHER',
        "description": 'Unspecified error'
    }
}

OCI_CAN_ERR_ALL = 0x0
for err_type in OCI_CAN_ERR_TYPES:
    OCI_CAN_ERR_ALL |= err_type


class OCI_TimerCapabilities(ct.Structure):
    """
    Static information of the device's timer.
    """
    _fields_ = [("localClockID", ct.c_char * 40),
                ("format", ct.c_uint32),
                ("tickFrequency", ct.c_uint32),
                ("ticksPerIncrement", ct.c_uint32),
                ("localStratumLevel", ct.c_uint32),
                ("localReferenceScale", ct.c_int),
                ("localTimeOriginIso8601", ct.c_char * 40),
                ("syncSlave", ct.c_uint32),
                ("syncMaster", ct.c_uint32)]


class OCI_CANControllerCapabilities(ct.Structure):
    """
    Specific structure for CAN controller capabilities.
    """
    _fields_ = [("samplesPerBit", ct.c_uint32),
                ("syncEdge", ct.c_uint32),
                ("physicalMedia", ct.c_uint32),
                ("reserved", ct.c_uint32),
                ("busEvents", ct.c_uint32),
                ("errorFrames", ct.c_uint32),
                ("messageFlags", ct.c_uint32),
                ("canFDSupport", ct.c_uint32),
                ("canFDMaxDataSize", ct.c_uint32),
                ("canFDMaxQualifiedDataRate", ct.c_uint32),
                ("canFDMaxDataRate", ct.c_uint32),
                ("canFDRxConfig_CANMode", ct.c_uint32),
                ("canFDRxConfig_CANFDMode", ct.c_uint32),
                ("canFDTxConfig_Mode", ct.c_uint32),
                ("canBusParticipationMode", ct.c_uint32)]

    @property
    def is_fd_capable(self):
        """
        :getter: Whether the device is CAN-FD capable or not.

        :type: bool
        """
        return self.canFDSupport & OCI_CANFDSUPPORT

    def __str__(self):
        res = "\n".join([
            "samplesPerBit:             " + str(hex(self.samplesPerBit)),
            "syncEdge:                  " + str(hex(self.syncEdge)),
            "physicalMedia:             " + str(hex(self.physicalMedia)),
            "busEvents:                 " + str(hex(self.busEvents)),
            "errorFrames:               " + str(hex(self.errorFrames)),
            "messageFlags:              " + str(hex(self.messageFlags)),
            "canFDSupport:              " + str(hex(self.canFDSupport))
        ])
        if self.is_fd_capable:
            res += "\n".join([
                "",
                "canFDMaxDataSize:          " + str(self.canFDMaxDataSize),
                "canFDMaxQualifiedDataRate: " + str(self.canFDMaxQualifiedDataRate),
                "canFDMaxDataRate:          " + str(self.canFDMaxDataRate),
                "canFDRxConfig_CANMode:     " + str(hex(self.canFDRxConfig_CANMode)),
                "canFDRxConfig_CANFDMode:   " + str(hex(self.canFDRxConfig_CANFDMode)),
                "canFDTxConfig_Mode:        " + str(hex(self.canFDTxConfig_Mode)),
                "canBusParticipationMode:   " + str(hex(self.canBusParticipationMode))
            ])
        return res

    def get_controller_capabilities(self):
        """
        Get controller capabilities as dictionary.

        For the exact meaning of the values, refer to the BOA documentation

        :rtype: dict[str, int]
        :return: controller_capabilities
        """
        controller_capabilities = {
            'samplesPerBit': self.samplesPerBit,
            'syncEdge': self.syncEdge,
            'physicalMedia': self.physicalMedia,
            'reserved': self.reserved,
            'busEvents': self.busEvents,
            'errorFrames': self.errorFrames,
            'messageFlags': self.messageFlags,
            'canFDSupport': self.canFDSupport
        }
        if self.is_fd_capable:
            controller_capabilities.update({
                'canFDMaxDataSize': self.canFDMaxDataSize,
                'canFDMaxQualifiedDataRate': self.canFDMaxQualifiedDataRate,
                'canFDMaxDataRate': self.canFDMaxDataRate,
                'canFDRxConfig_CANMode': self.canFDRxConfig_CANMode,
                'canFDRxConfig_CANFDMode': self.canFDRxConfig_CANFDMode,
                'canFDTxConfig_Mode': self.canFDTxConfig_Mode,
                'canBusParticipationMode': self.canBusParticipationMode
            })
        return controller_capabilities


class OCI_CANFDRxConfig(ct.Structure):
    """
    Represents the OCI_CAN FD Rx Configuration
    """
    _fields_ = [("canRxMode", ct.c_int),
                ("canFdRxMode", ct.c_int)]


class OCI_CANFDConfiguration(ct.Structure):
    """
    Represents a OCI_CAN FD Configuration.

    Please refer to the documentation of OCI_CANFDConfiguration structure in file
    ``Include\\OCI\\ocicanfd.h`` of your ETAS BOA installation folder for more information.

    :ivar dataSamplePoint:
        The data sample point in percent (0..100).
    :vartype dataSamplePoint: int

    :ivar dataBTL_Cycles:
        Data Bit Time Length cycles: number of time quanta in one bit.

        *Formula*:

        ``dataBTL_Cycles = sync_seg + data_prop_seg + data_phase_seg1 + data_phase_seg2``

        ``dataBTL_Cycles = sync_seg + data_tseg1 + data_tseg2``

        ``dataBTL_Cycles * dataSamplePoint / 100 = sync_seg + data_tseg1``

        ``sync_seg = 1``
    :vartype dataBTL_Cycles: int

    :ivar dataSJW:
        Data Sync Jump Width: length of the data sync segment.
    :vartype dataSJW: int

    :ivar flags:
        Specifies the enabled CAN-FD features of this controller. Valid values are OR-gated into
        the member.

        0x1: enable delay compensation, 0x2: enable non-ISO CAN FD (i.e. CAN FD 1.0
        specification as released by Bosch in 2012), 0x4 Disable protocol exceptions.
    :vartype flags: int

    :ivar txSecondarySamplePointOffset:
        The offset used for transceiver delay compensation, measured as a percentage of the data
        phase bit-time.  This is only valid when flags contains at least
        *OCI_CANFD_FLAG_TX_DELAY_COMPENSATION* (see OCI-Documentation).
    :vartype txSecondarySamplePointOffset: int
    """
    _fields_ = [("dataBitRate", ct.c_uint32),
                ("dataSamplePoint", ct.c_uint32),
                ("dataBTL_Cycles", ct.c_uint32),
                ("dataSJW", ct.c_uint32),
                ("flags", ct.c_uint32),
                ("txSecondarySamplePointOffset", ct.c_uint32),
                ("canFdRxConfig", OCI_CANFDRxConfig),
                ("canFdTxConfig", ct.c_int),
                ("txSecondarySamplePointFilterWindow", ct.c_uint16),
                ("reserved", ct.c_uint16)]

    def __str__(self):
        return "\n".join([
            "data_bitrate:                      " + str(self.dataBitRate) + "bps",
            "dataSamplePoint:                   " + str(self.dataSamplePoint) + "%",
            "dataBTL_Cycles:                    " + str(self.dataBTL_Cycles),
            "dataSJW:                           " + str(self.dataSJW),
            "flags:                             " + str(hex(self.flags)),
            "txSecondarySamplePointOffset:      " + str(self.txSecondarySamplePointOffset),
            "canFdRxConfig.canRxMode:           " + str(hex(self.canFdRxConfig.canRxMode)),
            "canFdRxConfig.canFdRxMode:         " + str(hex(self.canFdRxConfig.canFdRxMode)),
            "canFdTxConfig:                     " + str(hex(self.canFdTxConfig)),
            "txSecondarySamplePointFilterWindow:" + str(self.txSecondarySamplePointFilterWindow)
        ])

    def get_controller_fd_configuration(self):
        """
        Get controller FD configuration as dictionary.

        For the exact meaning of the values, please refer to the BOA documentation.

        :rtype: dict[str, int]
        :return: controller_fd_configuration
        """
        return {
            'data_bitrate': self.dataBitRate,
            'dataSamplePoint': self.dataSamplePoint,
            'dataBTL_Cycles': self.dataBTL_Cycles,
            'dataSJW': self.dataSJW,
            'flags': self.flags,
            'txSecondarySamplePointOffset': self.txSecondarySamplePointOffset,
            'canFdRxConfig.canRxMode': self.canFdRxConfig.canRxMode,
            'canFdRxConfig.canFdRxMode': self.canFdRxConfig.canFdRxMode,
            'canFdTxConfig': self.canFdTxConfig,
            'txSecondarySamplePointFilterWindow': self.txSecondarySamplePointFilterWindow
        }


class OCI_CANConfiguration(ct.Structure):
    """
    Represents a OCI_CAN Configuration.

    Please refer to the documentation of OCI_CANConfiguration structure in file
    ``Include\\OCI\\ocican.h`` of your ETAS BOA installation folder for more information.

    :ivar baudrate:
        Nominal Bitrate in bits/s.

        Not all Bitrates are supported. If the CAN controller can not be opened, try another
        bitrate.
    :vartype baudrate: int

    :ivar samplePoint:
        Nominal Sample point in percent (0 ... 100).
    :vartype samplePoint: int

    :ivar samplesPerBit:
        Number of samples per bit. 1 *(default)*: one sample per bit, 2: three samples per bit.
    :vartype samplesPerBit: int

    :ivar BTL_Cycles:
        Nominal Bit Time Length Cycles: number of time quanta in one bit.

        *Formula*:

        ``BTL_Cycles = sync_seg + prop_seg + phase_seg1 + phase_seg2``

        ``BTL_Cycles = sync_seg + nom_tseg1 + nom_tseg2``

        ``BTL_Cycles * samplePoint / 100 = sync_seg + nom_tseg1``

        ``sync_seg = 1``
    :vartype BTL_Cycles: int

    :ivar SJW:
        Nominal Synchronization Jump Width: length of the sync segment.
    :vartype SJW: int

    :ivar syncEdge:
        Synchronization edge flags. 1 *(default)*: single sync edge, 2: dual sync edge.
    :vartype syncEdge: int

    :ivar physicalMedia:
        Specify the CAN physical media to use. 1: high speed, 2: fault tolerant.
    :vartype physicalMedia: int

    :ivar selfReceptionMode:
        Specify whether the CAN controller / CAN controller firmware shall receive data sent through
        the same port. 0 *(default)*: self reception off, 1: self reception on.
    :vartype selfReceptionMode: int

    :ivar busParticipationMode:
        This member specifies how the controller behaves on the CAN bus. 1: bus mode passive
        (only listen/monitor), 2: bus mode active (listen/monitor/acknowledge/transmit).
    :vartype busParticipationMode: int

    :ivar canFDEnabled:
        0 *(default)*: Standard CAN, 1: CAN-FD.
    :vartype canFDEnabled: int

    :ivar can.interfaces.etas.OCI_CANFDConfiguration canFDConfig:
        CAN-FD parameters.

        Ignored if not using CAN-FD.
    :vartype canFDConfig: can.interfaces.etas.OCI_CANFDConfiguration
    """
    _fields_ = [("baudrate", ct.c_uint32),
                ("samplePoint", ct.c_uint32),
                ("samplesPerBit", ct.c_uint32),
                ("BTL_Cycles", ct.c_uint32),
                ("SJW", ct.c_uint32),
                ("syncEdge", ct.c_uint32),
                ("physicalMedia", ct.c_uint32),
                ("selfReceptionMode", ct.c_uint32),
                ("busParticipationMode", ct.c_uint32),
                ("canFDEnabled", ct.c_uint32),
                ("canFDConfig", OCI_CANFDConfiguration)]

    def __str__(self):
        res = "\n".join([
            "baudrate:                          " + str(self.baudrate) + "bps",
            "samplePoint:                       " + str(self.samplePoint) + "%",
            "samplesPerBit:                     " + str(hex(self.samplesPerBit)),
            "BTL_Cycles:                        " + str(self.BTL_Cycles),
            "SJW:                               " + str(self.SJW),
            "syncEdge:                          " + str(hex(self.syncEdge)),
            "physicalMedia:                     " + str(hex(self.physicalMedia)),
            "selfReceptionMode:                 " + str(hex(self.selfReceptionMode)),
            "busParticipationMode:              " + str(hex(self.busParticipationMode)),
            "canFDEnabled:                      " + str(hex(self.canFDEnabled))
        ])
        if self.canFDEnabled:
            res += "\n" + str(self.canFDConfig)
        return res

    def get_controller_configuration(self):
        """
        Get controller configuration as dictionary.

        For the exact meaning of the values, please refer to the BOA documentation.

        :rtype: dict[str, int]
        :return: controller_configuration
        """
        res = {
            'baudrate': self.baudrate,
            'samplePoint': self.samplePoint,
            'samplesPerBit': self.samplesPerBit,
            'BTL_Cycles': self.BTL_Cycles,
            'SJW': self.SJW,
            'syncEdge': self.syncEdge,
            'physicalMedia': self.physicalMedia,
            'selfReceptionMode': self.selfReceptionMode,
            'busParticipationMode': self.busParticipationMode,
            'canFDEnabled': self.canFDEnabled
        }
        if self.canFDEnabled:
            res.update(self.canFDConfig.get_controller_fd_configuration())
        return res


class OCI_CANRxFilter(ct.Structure):
    """
    Represents a OCI_CAN Rx Filter
    """
    _fields_ = [("frameIDValue", ct.c_uint32),
                ("frameIDMask", ct.c_uint32),
                ("tag", ct.c_uint32)]


class OCI_CANRxFilterEx(ct.Structure):
    """
    Represents a OCI_CAN Rx Extended Filter
    """
    _fields_ = [("frameIDValue", ct.c_uint32),
                ("frameIDMask", ct.c_uint32),
                ("tag", ct.c_uint32),
                ("flagsValue", ct.c_uint16),
                ("flagsMask", ct.c_uint16)]


class OCI_CANEventFilter(ct.Structure):
    """
    Represents a OCI_CAN Event Filter
    """
    _fields_ = [("eventCode", ct.c_uint32),
                ("tag", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_CANErrorFrameFilter(ct.Structure):
    """
    Represents a OCI_CAN Error Frame Filter
    """
    _fields_ = [("errorFrame", ct.c_uint32),
                ("tag", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_CANTxMessage(ct.Structure):
    """
    Represents a OCI_CAN Tx Message
    """
    _fields_ = [("frameID", ct.c_uint32),
                ("flags", ct.c_uint16),
                ("__padding__", ct.c_uint8),
                ("dlc", ct.c_uint8),
                ("data", CanData)]


class OCI_CANFDTxMessage(ct.Structure):
    """
    Represents a OCI_CAN FD Tx Message
    """
    _fields_ = [("frameID", ct.c_uint32),
                ("flags", ct.c_uint16),
                ("__padding__", ct.c_uint8),
                ("size", ct.c_uint8),
                ("data", CanDataFD)]


class OCI_CANRxMessage(ct.Structure):
    """
    Represents a OCI_CAN Rx Message
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("frameID", ct.c_uint32),
                ("flags", ct.c_uint16),
                ("__padding1__", ct.c_uint8),
                ("size", ct.c_uint8),
                ("__padding2__", ct.c_uint32),
                ("data", CanDataFD)]


# Merged canFDRxMessage and rxMessage
# class OCI_CANFDRxMessage(OCI_CANRxMessage)


class OCI_CANErrorFrameMessage(ct.Structure):
    """
    Represents a OCI_CAN ErrorFrameMessage
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("frameID", ct.c_uint32),
                ("flags", ct.c_uint16),
                ("__padding__", ct.c_uint8),
                ("size", ct.c_uint8),
                ("type", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_CANEventMessage(ct.Structure):
    """
    Represents a OCI_CAN EventMessage
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("eventCode", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_InternalErrorEventMessage(ct.Structure):
    """
    Represents a OCI_InternalErrorEventMessage
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("eventCode", ct.c_uint32),
                ("errorCode", OCI_ErrorCode)]


class OCI_TimerEventMessage(ct.Structure):
    """
    Represents a OCI_TimerEventMessage
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("eventCode", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_QueueEventMessage(ct.Structure):
    """
    Represents a OCI_QueueEventMessage
    """
    _fields_ = [("timeStamp", OCI_Time),
                ("tag", ct.c_uint32),
                ("eventCode", ct.c_uint32),
                ("destination", ct.c_uint32)]


class OCI_CANMessageDataEx(ct.Union):
    """
    Shared structure of CAN bus relevant data.
    """
    _fields_ = [
        ("rxMessage", OCI_CANRxMessage),
        ("txMessage", OCI_CANTxMessage),
        ("errorFrameMessage", OCI_CANErrorFrameMessage),
        ("canEventMessage", OCI_CANEventMessage),
        ("internalErrorEventMessage", OCI_InternalErrorEventMessage),
        ("timerEventMessage", OCI_TimerEventMessage),
        ("queueEventMessage", OCI_QueueEventMessage),
        # ("canFDRxMessage", OCI_CANFDRxMessage), # Merged canFDRxMessage and rxMessage
        ("canFDTxMessage", OCI_CANFDTxMessage)
    ]


class OCI_CANMessageEx(ct.Structure):
    """
    Represents a OCI_CAN MessageEx
    """
    _fields_ = [("type", OCI_CANMessageDataType),
                ("reserved", ct.c_uint32),
                ("data", OCI_CANMessageDataEx)]


class OCI_CANRxCallbackSingleMsg(ct.Structure):
    """
    Callback for CAN event and message handling
    """
    #In BOA, userData type is void*. Using ct.POINTER(ct.py_object)
    #instead of c_void_p for convenience (i.e. avoids ugly casting
    #later on)
    _fields_ = [("function",
                 ct.CFUNCTYPE(None, ct.POINTER(ct.py_object),
                              ct.POINTER(OCI_CANMessageEx))),
                ("userData", ct.POINTER(ct.py_object))]


class OCI_CANControllerProperties(ct.Structure):
    """
    Specific structure for OCI CAN controller properties.
    """
    _fields_ = [("mode", ct.c_int)]


class OCI_CANTxQueueConfiguration(ct.Structure):
    """
    Specific structure for the OCI CAN TX queue configuration.
    """
    _fields_ = [("reserved", ct.c_uint32)]


class OCI_CANRxQueueConfiguration(ct.Structure):
    """
    Specific structure for the OCI CAN RX queue configuration.
    """
    _fields_ = [("onFrame", OCI_CANRxCallbackSingleMsg),
                ("onEvent", OCI_CANRxCallbackSingleMsg),
                ("selfReceptionMode", ct.c_uint32)]


#///////////////////////////////////////////////////////////
# Methods definitions
#///////////////////////////////////////////////////////////


@ct.CFUNCTYPE(None, ct.POINTER(ct.py_object), ct.POINTER(OCI_CANMessageEx))
def event_callback(user_data, msg):
    """
    Bus Event and Error Frame Callback Function
    """
    self = user_data.contents.value

    if msg.contents.type == OCI_CAN_BUS_EVENT.value:
        timestamp = self.tick_to_time(msg.contents.data.canEventMessage.timeStamp)
        event = OCI_CAN_BUS_EVENTS[msg.contents.data.canEventMessage.eventCode]
        if event['BusState'] is not None:
            if self.bus_state == event['BusState']:
                # Bus state did not change. Directly return to avoid spamming the logger.
                return
            self.bus_state = event['BusState']
        self.logger.info("Hardware Timestamp: %.6f, BUS EVENT: %s",
                         timestamp, event['description'])

    elif msg.contents.type == OCI_CAN_ERROR_FRAME.value:
        timestamp = self.tick_to_time(msg.contents.data.errorFrameMessage.timeStamp)
        errortype = OCI_CAN_ERR_TYPES[msg.contents.data.errorFrameMessage.type]['description']
        self.logger.info("Hardware Timestamp: %.6f, BUS ERROR FRAME: %s, FrameID: %s",
                         timestamp, errortype, msg.contents.data.errorFrameMessage.frameID)

    elif msg.contents.type == OCI_CAN_INTERNAL_ERROR_EVENT.value:
        timestamp = self.tick_to_time(msg.contents.data.internalErrorEventMessage.timeStamp)
        self.logger.info("Hardware Timestamp: %.6f, INTERNAL ERROR EVENT: %s",
                         timestamp, hex(msg.contents.data.internalErrorEventMessage.eventCode))

    else:
        self.logger.warning("Unexpected Msg type in event_callback: %s" %
                            hex(msg.contents.type))


class EtasMessage(can.Message):
    """
    Adds the attribute ``is_self_reception`` to :class:`can.Message` so that we are able to
    differentiate between our own Tx messages being loopback and normal Rx messages.
    """

    # Deactivate pylint too-many-arguments (R0913) and too-many-locals (R0914). Rationale: this
    # class inherits from can.Message which already has an equivalent number of arguments.
    def __init__(  # pylint: disable=(too-many-arguments, too-many-locals)
            self,
            timestamp=0.0,
            arbitration_id=0,
            is_extended_id=None,
            is_remote_frame=False,
            is_error_frame=False,
            channel=None,
            dlc=None,
            data=None,
            is_fd=False,
            bitrate_switch=False,
            error_state_indicator=False,
            extended_id=None,  # deprecated in 3.x, TODO remove in 4.x
            check=False,
            is_self_reception=False,
            dlc_is_len=False):
        """
        :param bool is_self_reception:
            Differentiate between the normal Rx messages (``False``) and our own Tx messages being
            loopback (``True``). If attribute
            :attr:`can.interfaces.etas.EtasBus.receive_own_messages` is ``False``, no loopback
            messages will be receive and thus
            :attr:`~can.interfaces.etas.EtasMessage.is_self_reception` will also always be
            ``False``.

            This attribute is set by :meth:`can.interfaces.etas.EtasBus._recv_internal`. If set by
            the user, it will be ignored by :meth:`can.interfaces.etas.EtasBus.send` because it is
            only relevant for received messages.

        :param others: Please refer to :class:`can.Message`.
        """
        self.is_self_reception = is_self_reception
        self.dlc_is_len = dlc_is_len
        if dlc is None:
            if dlc_is_len:  # Uses python-can convention.
                self.dlc = len(self.data)
            else:  # Make sure that we send the DLC as defined in ISO 11898-1 and not the length.
                self.dlc = can.util.len2dlc(len(self.data))
        super().__init__(timestamp, arbitration_id, is_extended_id,
                         is_remote_frame, is_error_frame, channel, dlc, data,
                         is_fd, bitrate_switch, error_state_indicator,
                         extended_id, check)

    def __str__(self):
        field_strings = ["Timestamp: {0:>15.6f}".format(self.timestamp)]
        if self.is_extended_id:
            arbitration_id_string = "ID: {0:08x}".format(self.arbitration_id)
        else:
            arbitration_id_string = "ID: {0:04x}".format(self.arbitration_id)
        field_strings.append(arbitration_id_string.rjust(12, " "))

        flag_string = " ".join([
            "Tx" if self.is_self_reception else "Rx",
            "-",
            "X" if self.is_extended_id else "S",
            "E" if self.is_error_frame else " ",
            "R" if self.is_remote_frame else " ",
            "F" if self.is_fd else " ",
            "BS" if self.bitrate_switch else "  ",
            "EI" if self.error_state_indicator else "  "
        ])

        field_strings.append(flag_string)

        field_strings.append("DLC: {0:2d}".format(self.dlc))
        data_strings = []
        if self.data is not None:
            for index in range(0, min(self.dlc if self.dlc_is_len else can.util.dlc2len(self.dlc),
                                      len(self.data))):
                data_strings.append("{0:02x}".format(self.data[index]))
        if data_strings:  # if not empty
            field_strings.append(" ".join(data_strings).ljust(24, " "))
        else:
            field_strings.append(" " * 24)

        if (self.data is not None) and (self.data.isalnum()):
            field_strings.append("'{}'".format(
                self.data.decode('utf-8', 'replace')))

        if self.channel is not None:
            try:
                field_strings.append("Channel: {}".format(self.channel))
            except UnicodeEncodeError:
                pass

        return "    ".join(field_strings).strip()


class EtasCSI():
    """
    Interface to ETAS CSI (Connection Service Interface).

    The CSI provides functionality to dynamically search all connected hardware.
    """

    @staticmethod
    def enumerate_controllers():
        """
        Search for connected CAN devices.

        :rtype: list[str]
        :return: all found CAN devices.
        """
        controller_list = []

        node_range = CSI_NodeRange(CSI_NODE_MIN, CSI_NODE_MAX)
        csi_tree = ct.pointer(CSI_Tree())
        error_code = OCI_ErrorCode(
            dll_csi_bind.CSI_CreateProtocolTree("", node_range,
                                                ct.byref(csi_tree)))
        EtasOCI.static_fail_check(error_code,
                                  function_name="CSI_CreateProtocolTree",
                                  reason="Failed to create the Protocol Tree")

        uri_prefix = 'ETAS:/'
        protocol = 'CAN:'
        EtasCSI._csi_tree_traversal(protocol, csi_tree, uri_prefix, controller_list)

        error_code = OCI_ErrorCode(dll_csi_bind.CSI_DestroyProtocolTree(csi_tree))
        EtasOCI.static_fail_check(error_code,
                                  function_name="CSI_DestroyProtocolTree",
                                  reason="Failed to destroy the Protocol Tree")

        if not controller_list:
            raise EtasError("No CAN Controllers have been found. Please ensure that your "
                            "device is connected and that you have installed its driver.\n")

        return controller_list

    @staticmethod
    def _csi_tree_traversal(protocol, csi_tree, uri_prefix, controller_list):
        """
        Recursively explore the CSI tree and store the CAN controllers in controller_list.
        """
        uri_name = ct.c_char_p(csi_tree.contents.item.uri_name).value.decode()

        if uri_name.startswith(protocol):
            controller_list.append(uri_prefix + '/' + uri_name)

        if csi_tree.contents.child:
            new_uri_prefix = uri_prefix
            new_uri_prefix += '/'
            new_uri_prefix += ct.c_char_p(csi_tree.contents.item.uri_name).value.decode()
            EtasCSI._csi_tree_traversal(protocol, csi_tree.contents.child,
                                        new_uri_prefix, controller_list)

        if csi_tree.contents.sibling:
            EtasCSI._csi_tree_traversal(protocol, csi_tree.contents.sibling,
                                        uri_prefix, controller_list)

    @staticmethod
    def print_controllers(controller_list):
        """
        Print all found CAN devices.
        """
        if controller_list is None:
            controller_list = EtasCSI.enumerate_controllers()

        print("-------------------------------------------------------------------------------")
        print("Connected devices found are: ")
        for i in controller_list:
            print("[{}] ".format(controller_list.index(i)), i)
        print("-------------------------------------------------------------------------------")

    @staticmethod
    def _controller_index_to_uri(controller_list, index):
        """
        Convert the ``index`` value of a controller into its string representation.

        :param int index:
            Specifies the position the channel in the list of connected can devices.

        :rtype: str
        :return: A string representation of the channel.

        :raise can.interfaces.etas.EtasError:
            If index is out of bounds.
        """
        try:
            channel = controller_list[index]
        except:
            global_logger.error("Index value %d is out of range (valid values: 0..%d). Is the "
                                "device connected?", index, len(controller_list) - 1)
            EtasCSI.print_controllers(controller_list)
            raise EtasError("Index value {} is out of range (valid values: 0..{})."
                            .format(index, len(controller_list) - 1))
        return channel

    @staticmethod
    def find_controller(index):
        """
        Find a controller from its index value.

        :param int,None index:
            Specifies the position the channel in the list of connected can devices. If this
            parameter is omitted, automatically triggers an interactive menu.

        :rtype: str
        :return: A string representation of the channel.

        :raise can.interfaces.etas.EtasError:
            If ``index`` is out of bounds.
        """
        if index is None:
            channel = EtasCSI.select_controller()
        else:
            channel = EtasCSI._controller_index_to_uri(EtasCSI.enumerate_controllers(),
                                                       index)

        return channel

    @staticmethod
    def select_controller():
        """
        Trigger an interactive menu that will list the connected devices and ask user to select one.

        :rtype: str
        :return: A string representation of the channel.
        """
        controller_list = EtasCSI.enumerate_controllers()
        EtasCSI.print_controllers(controller_list)

        index = None
        while not isinstance(index, int):
            print("Specify the index of the channel you want to use:")
            try:
                index = int(input())
            except ValueError:
                print("Please put in a number!")
                continue
            try:
                channel = EtasCSI._controller_index_to_uri(controller_list, index)
            except EtasError:
                print("Index value {} is out of range (valid values: 0..{}).".
                      format(index,
                             len(controller_list) - 1))
                index = None

        return channel

# Deactivate pylint too-many-instance-attributes (R0902). Rationale: those attributes are needed to
# open and interact with a CAN bus through the ETAS OCI interface.
class EtasOCI(EtasCSI):  # pylint: disable=too-many-instance-attributes
    """
    Interface to ETAS OCI (Open Controller Interface).

    The OCI provides functionality to interact with the controller.
    """
    def __init__(self, channel=None):
        self.boa_api_version = None
        self.oci_handle = None
        self.oci_filters = None
        self.oci_timer_capabilities = None
        self.oci_can_controller_capabilities = None
        self.oci_can_configuration = None
        self.oci_tx_queue = None
        self.oci_rx_queue = None

        # Below attributes are only used once to feed their respective function. However, BOA
        # expect the data not to be freed. For this reason, we declare these as attributes of self
        # so that Python's garbage collector does not destroy them.
        self.ctrl_prop = None
        self.tx_q_conf = None
        self.rx_q_conf = None
        self.event_filter = None
        self.error_frame_filter = None

        if isinstance(channel, int) or channel is None:
            self.channel_info = self.find_controller(channel)
        else:
            self.channel_info = channel

        extra = {'channel': self.channel_info}
        handler.setFormatter(logging.Formatter(FORMAT_HEADER + '%(channel)s: %(message)s'))
        global_logger.addHandler(handler)
        self.logger = logging.LoggerAdapter(global_logger, extra)


    def _check_boa_api_version(self, expected_version):
        """
        Some OCI features require a specific BOA API version, so this function is used to verify if
        the used API version satisfies the features requirements.
        """
        return self.boa_api_version >= expected_version

    def _time_to_tick(self, time):
        """
        Convert a time in second to the device tickstamp format.

        :param float time: The time in second.

        :rtype: ctypes.c_int64
        :return: Device's time expressed in ticks.
        """
        return ct.c_int64(int(time) * self.oci_timer_capabilities.tickFrequency)

    def tick_to_time(self, tick):
        """
        Convert the device tickstamp format to a time in second.

        :param ctypes.c_int64 tick: Device's time expressed in ticks.

        :rtype: float
        :return: The time in second.
        """
        return tick / self.oci_timer_capabilities.tickFrequency

    @staticmethod
    def _oci_exec(function_name, *args):
        """
        Call a function from the OCI DLL.

        :param str function_name: Name of the function to be called.

        :param args: Arguments to be passed to the DLL function.

        :rtype: can.interfaces.etas.OCI_ErrorCode
        :return: The OCI error code.
        """
        function = getattr(dll_ocd_proxy, function_name)
        return OCI_ErrorCode(function(*args))

    def _oci_exec_check(self,
                        function_name: str,
                        do_shutdown: bool,
                        fail_reason: str,
                        *args):
        """
        Call a function from the OCI DLL and check its return error code.

        :param str function_name: Name of the function to be called.

        :param bool do_shutdown: Do we need to shutdown the controller if an error occurs?

        :param str fail_reason: Message to be printed in the logger in case of failure.

        :param args: Arguments to be passed to the DLL function.
        """
        error_code = self._oci_exec(function_name, *args)
        self._fail_check(error_code=error_code,
                         function_name=function_name,
                         reason=fail_reason,
                         do_shutdown=do_shutdown)

    @staticmethod
    def _get_error_fallback(error_value):
        """
        Unfortunately, OCI_GetError() does not always have a human readable entry for each of the
        error codes... This function tries to remediate that by returning locally defined error
        messages.

        :rtype: str
        :return: Human readable error description.
        """

        fallback_error_code = OCI_ERR_CODE.get(error_value)
        if fallback_error_code is not None:
            return ("Error name: " + fallback_error_code['name'] +
                    ", Description: " + fallback_error_code['description'])

        fallback_error_type = OCI_ERR_TYPE.get(error_value & OCI_ERR_TYPE_MASK)
        if fallback_error_type is not None:
            return ("Error type: " + fallback_error_type['name'] +
                    ", Description: " + fallback_error_type['description'])

        return "No description available for error code: {}.".format(hex(error_value))

    @staticmethod
    def _oci_get_error(error_code, function_name, logger=global_logger, oci_handle=OCI_NO_HANDLE):
        """
        :rtype: str
        :return: Human readable error description.
        """
        oci_error_string_length = ct.c_uint32(OCI_ERROR_STRING_LENGTH)
        utf8_text = ct.create_string_buffer(oci_error_string_length.value)

        if error_code.value & OCI_ERR_FLAG_WARNING:
            logger.info("Function name: %s, Error code: %s", function_name,
                        hex(error_code.value))
        elif error_code.value & OCI_ERR_FLAG_ERROR:
            logger.error("Function name: %s, Error code: %s", function_name,
                         hex(error_code.value))
        else:
            logger.error("Error code is: %s", hex(error_code.value))
            raise EtasError("UNKNOWN ERROR")

        get_err_ret = EtasOCI._oci_exec("OCI_GetError",
                                        oci_handle, error_code, utf8_text, oci_error_string_length)

        if get_err_ret.value == OCI_SUCCESS:
            return "Description: " + utf8_text.value.decode() + '.'
        return EtasOCI._get_error_fallback(error_code.value)

    @staticmethod
    def static_fail_check(error_code,
                          function_name,
                          reason="OCI_Errorcode",
                          logger=global_logger,
                          oci_handle=OCI_NO_HANDLE):
        """
        Checks that the BOA API functions got executed without an error and specifies the reason.
        """
        error_value = error_code.value
        if error_value != OCI_SUCCESS:
            if error_value & OCI_ERR_FLAG_WARNING:
                local_logger = logger.info
            elif error_value & OCI_ERR_FLAG_ERROR:
                local_logger = logger.error
            else:
                local_logger = logger.info

            error_text = EtasOCI._oci_get_error(error_code, function_name, logger, oci_handle)
            local_logger(error_text)
            if error_value & OCI_ERR_TYPE_MASK == OCI_ERR_TYPE_RESERVED:
                local_logger("Try to update both BOA and your device firmware to the latest "
                             "version available.")

            if error_value & OCI_ERR_FLAG_ERROR:
                if error_value == OCI_ERR_INCONSISTENT_PARAMETER_SET:
                    return  #Not a critical error
                raise EtasError(reason)

    def _fail_check(self,
                    error_code,
                    function_name,
                    reason="OCI_Errorcode",
                    do_shutdown=False):
        """
        Checks that the BOA API functions got executed without an error and specifies the reason.
        """
        error_value = error_code.value
        if error_value != OCI_SUCCESS:
            try:
                self.static_fail_check(error_code, function_name, reason,
                                       self.logger, self.oci_handle)
            except EtasError:
                if do_shutdown:
                    self.shutdown()
                raise

    def _oci_create_can_controller_version(self, boa_api_version):
        """
        Try to create a CAN controller for a given BOA API version.

        :param can.interfaces.etas.BOA_API_Version boa_api_version:
            BOA API version to be tested.

        :rtype: bool
        :return:
            ``True`` if the BOA API version is supported and the controller is successfully
            created, else return ``False``.
        """
        uri_name = ct.c_char_p(self.channel_info.encode())
        self.logger.debug("Creating a controller instance")
        error_code = self._oci_exec("OCI_CreateCANControllerVersion", uri_name,
                                    ct.byref(boa_api_version), ct.byref(self.oci_handle))
        if error_code.value in [OCI_ERR_PROTOCOL_VERSION_NOT_SUPPORTED,
                                OCI_ERR_NO_INTERFACE]:
            return False
        self._fail_check(error_code,
                         function_name="OCI_CreateCANControllerVersion",
                         reason="Failed to create the CAN controller",
                         do_shutdown=True)
        return True

    def _oci_create_can_controller(self, requested_api=None):
        """
        Create a CAN controller.

        If the BOA API is not provided, automatically detect the highest supported API version.

        If the provided BOA API is not supported, decrement the minor version number until a
        supported API version is found.

        :param can.interfaces.etas.BOA_API_Version requested_api:
            BOA API version as requested by the user.
        """
        if self.oci_handle is None:
            self.oci_handle = OCI_ControllerHandle(OCI_NO_HANDLE)
        if self.oci_handle.value != OCI_NO_HANDLE:
            return

        if self.boa_api_version is not None:
            # Device is restarting, reusing BOA API version from previous run.
            if not self._oci_create_can_controller_version(self.boa_api_version):
                raise EtasError("Unexpected error: BOA API version {} was previously accepted but "
                                "now is rejected?!".format(self.boa_api_version))
            return

        if requested_api is not None:
            self.boa_api_version = requested_api.copy()
        else:
            self.boa_api_version = LATEST_BOA_API.copy()

        self.logger.debug("Trying BOA API version %s", self.boa_api_version)
        while not self._oci_create_can_controller_version(self.boa_api_version):
            self.boa_api_version.decrement()
            self.logger.debug("Trying BOA API version %s", self.boa_api_version)

        if requested_api is not None and requested_api != self.boa_api_version:
            self.logger.warning("Requested BOA API version %s is not supported by your "
                                "controller. Downgraded to BOA API version %s",
                                requested_api, self.boa_api_version)
        else:
            self.logger.info("Using BOA API version %s", self.boa_api_version)

    def _oci_destroy_can_controller(self):
        """
        Destroy the CAN controller including its attached resources such as the Rx and Tx queues.
        """
        if self.oci_handle is not None and self.oci_handle.value != OCI_NO_HANDLE:
            self.logger.debug("Destroying the controller instance")
            self._oci_exec_check("OCI_DestroyCANController", False,
                                 "Failed to destroy the CAN Controller", self.oci_handle)
            self.oci_filters = None
            self.oci_handle = OCI_ControllerHandle(OCI_NO_HANDLE)
        else:
            self.logger.warning("The controller instance has already been destroyed")

    def _oci_open_can_controller(self):
        """
        Start the CAN Controller.
        """
        self.ctrl_prop = OCI_CANControllerProperties(mode=OCI_CONTROLLER_MODE_RUNNING)
        error_code = self._oci_exec("OCI_OpenCANController", self.oci_handle,
                                    ct.byref(self.oci_can_configuration), ct.byref(self.ctrl_prop))
        if error_code.value == OCI_WARN_PARAM_ADAPTED:
            # Save the adapted configuration so that the user can access it with
            # {get,print}_controller_configuration(). Also useful if we need to restart the
            # controller.
            self._oci_get_can_configuration()
        self._fail_check(error_code,
                         function_name="OCI_OpenCANController",
                         reason="Failed to open the CAN controller",
                         do_shutdown=True)

    def _oci_close_can_controller(self):
        """
        Stop the CAN Controller.
        """
        self.oci_filters = None
        self._oci_destroy_can_tx_queue()
        self._oci_destroy_can_rx_queue()
        self._oci_exec_check("OCI_CloseCANController", False,
                             "Failed to close the CAN controller", self.oci_handle)

    def _oci_get_timer_capabilities(self):
        """
        Get the controller's timer capabilities.
        """
        if self.oci_timer_capabilities is None:
            self.oci_timer_capabilities = OCI_TimerCapabilities()
            self._oci_exec_check("OCI_GetTimerCapabilities", True,
                                 "Failed to get the CAN controller's timer capabilities",
                                 self.oci_handle, ct.byref(self.oci_timer_capabilities))

    def _oci_get_controller_capabilities(self):
        """
        Get the controller capabilities.
        """
        if self.oci_can_controller_capabilities is None:
            self.oci_can_controller_capabilities = OCI_CANControllerCapabilities()
            self._oci_exec_check("OCI_GetCANControllerCapabilities", True,
                                 "Failed to get CAN controller capabilities",
                                 self.oci_handle, ct.byref(self.oci_can_controller_capabilities))

    def _oci_get_can_configuration(self):
        """
        Get the controller configuration: if the controller is already used by another application,
        gets the current running configuration, else, use a blank configuration.

        :rtype: bool
        :return:
            Whether the controller is already configured by another program (``True``) or not
            (``False``).
        """
        tmp_oci_can_conf = OCI_CANConfiguration()
        is_used_by_another_program = False

        error_code = self._oci_exec("OCI_GetCANConfiguration",
                                    self.oci_handle, ct.byref(tmp_oci_can_conf))
        if error_code.value == OCI_SUCCESS:
            can_capabilities = self.oci_can_controller_capabilities
            if ((tmp_oci_can_conf.baudrate == 0) or
                    (tmp_oci_can_conf.samplesPerBit & ~can_capabilities.samplesPerBit) or
                    (tmp_oci_can_conf.syncEdge & ~can_capabilities.syncEdge) or
                    (tmp_oci_can_conf.physicalMedia & ~can_capabilities.physicalMedia)):
                self.logger.debug("Current configuration is incoherent. Ignoring it and "
                                  "continuing with provided configuration.")
                self.oci_can_configuration = OCI_CANConfiguration()
            else:
                self.oci_can_configuration = tmp_oci_can_conf
                is_used_by_another_program = True
        elif error_code.value != OCI_ERR_NO_CONFIG:
            self._fail_check(error_code,
                             function_name="OCI_GetCANConfiguration",
                             reason="Failed to get CAN controller configuration",
                             do_shutdown=True)
        return is_used_by_another_program

    def _oci_create_can_tx_queue(self):
        """
        Create a transmission queue for the controller.
        """
        self.tx_q_conf = OCI_CANTxQueueConfiguration()
        self.oci_tx_queue = OCI_QueueHandle()
        self._oci_exec_check("OCI_CreateCANTxQueue", True, "Failed to create the CAN Tx Queue",
                             self.oci_handle, ct.byref(self.tx_q_conf),
                             ct.byref(self.oci_tx_queue))

    def _oci_destroy_can_tx_queue(self):
        """
        Destroy the transmission queue of the controller.
        """
        if self.oci_tx_queue is not None:
            self._oci_exec_check("OCI_DestroyCANTxQueue", False,
                                 "Failed to destroy the CAN Tx Queue", self.oci_tx_queue)
            self.oci_tx_queue = None

    def _oci_create_can_rx_queue(self,
                                 event_call_back=OCI_CANRxCallbackSingleMsg(),
                                 receive_own_messages=False):
        """
        Create a reception queue for the controller and set up the Event callback function.

        :param can.interfaces.etas.OCI_CANRxCallbackSingleMsg event_call_back: A callback function
        that will be triggered for the Event and Error frames according to the event and error
        filter parameters (c.f. the two functions below).
        :param bool receive_own_messages: Whether message loopback is activated (``True``) or not
        (``False``).
        """
        self.rx_q_conf = OCI_CANRxQueueConfiguration(
            onFrame=OCI_CANRxCallbackSingleMsg(),
            onEvent=event_call_back,
            selfReceptionMode=(OCI_SELF_RECEPTION_ON if receive_own_messages
                               else OCI_SELF_RECEPTION_OFF)
        )
        self.oci_rx_queue = OCI_QueueHandle()
        self._oci_exec_check("OCI_CreateCANRxQueue", True, "Failed to create the CAN Rx Queue",
                             self.oci_handle, ct.byref(self.rx_q_conf),
                             ct.byref(self.oci_rx_queue))

    def _oci_destroy_can_rx_queue(self):
        """
        Destroy the reception queue of the controller.
        """
        if self.oci_rx_queue is not None:
            self._oci_exec_check("OCI_DestroyCANRxQueue", False,
                                 "Failed to destroy the CAN Rx Queue",
                                 self.oci_rx_queue)
            self.oci_rx_queue = None

    def _oci_add_can_bus_event_filter(self):
        """
        Configure the event filter. The Event callback function (c.f.
        :meth:`~can.interfaces.etas.EtasOCI._oci_create_can_rx_queue`) will be triggered for each
        of the events added to the filter. By default, this function adds all the events supported
        by the controller.
        """
        if self.event_filter is None:
            event_code = OCI_CAN_BUS_EVENT_ALL
            if event_code != self.oci_can_controller_capabilities.busEvents:
                for event in OCI_CAN_BUS_EVENTS:
                    if self.oci_can_controller_capabilities.busEvents & event == 0:
                        self.logger.info("Bus event filter %s (%s) is not supported",
                                         OCI_CAN_BUS_EVENTS[event]['name'],
                                         OCI_CAN_BUS_EVENTS[event]['description'])
                        event_code &= ~event
            self.event_filter = OCI_CANEventFilter(
                eventCode=ct.c_uint32(event_code),
                tag=0,
                destination=OCI_EVENT_DESTINATION_CALLBACK
            )
        self._oci_exec_check("OCI_AddCANBusEventFilter", False,
                             "Failed to add the Event Filter to the Rx Queue",
                             self.oci_rx_queue, ct.byref(self.event_filter), 1)

    def _oci_add_can_bus_error_frame_filter(self):
        """
        Configure the error filter. The Event callback function (c.f.
        :meth:`~can.interfaces.etas.EtasOCI._oci_create_can_rx_queue`) will be triggered for each
        of the events added to the filter. By default, this function adds all the errors.
        """
        self.error_frame_filter = OCI_CANErrorFrameFilter(
            eventCode=OCI_CAN_ERR_ALL,
            tag=0,
            destination=OCI_EVENT_DESTINATION_CALLBACK
        )
        self._oci_exec_check("OCI_AddCANErrorFrameFilter", False,
                             "Failed to add the Error Frame Filter to the Rx Queue",
                             self.oci_rx_queue, ct.byref(self.error_frame_filter), 1)

    def _oci_read_can_data(self, timeout):
        """
        Pop a CAN message from the reception queue.

        :param float timeout:
            Max time to wait in seconds or None if infinite, should not be negative.
        """
        count = ct.c_uint32()
        rx_message = OCI_CANMessageEx()
        ptr_rx_message_ex = ct.pointer(rx_message)

        oci_timeout = OCI_NO_TIME if timeout is None or timeout < 0 else self._time_to_tick(timeout)
        if timeout < 0:
            self.logger.error("Timeout is negative (%s)! Ignoring its value and waiting "
                              "indefinitely!", timeout)

        if self._check_boa_api_version(BOA_API_Version(1, 3, 0, 0)):
            self._oci_exec_check("OCI_ReadCANDataEx", True, "Failed to read CAN Data",
                                 self.oci_rx_queue, oci_timeout,
                                 ct.byref(ptr_rx_message_ex), 1, ct.byref(count), None)
        else:
            self._oci_exec_check("OCI_ReadCANData", True, "Failed to read CAN Data",
                                 self.oci_rx_queue, oci_timeout,
                                 ptr_rx_message_ex, 1, ct.byref(count), None)
        if count.value > 1:
            raise EtasError("Bulk receive is not supported , this code should not be reached.")
        return rx_message, count.value == 1

    def _oci_write_can_data(self, oci_can_msg):
        """
        Push a CAN message to the transmission queue.

        :param can.interfaces.etas.OCI_CANMessageEx oci_can_msg: The message to be sent.
        """
        ptr_can_msg = ct.pointer(oci_can_msg)
        if self._check_boa_api_version(BOA_API_Version(1, 3, 0, 0)):
            self._oci_exec_check("OCI_WriteCANDataEx", True, "Failed to write CAN Data",
                                 self.oci_tx_queue, OCI_NO_TIME, ct.byref(ptr_can_msg), 1, None)
        else:
            self._oci_exec_check("OCI_WriteCANData", True, "Failed to write CAN Data",
                                 self.oci_tx_queue, OCI_NO_TIME, ptr_can_msg, 1, None)

    def _oci_add_can_frame_filter(self):
        """
        Set up the CAN frame filters.
        """
        if self._check_boa_api_version(BOA_API_Version(1, 4, 0, 0)):
            add_can_frame_filter_function = "OCI_AddCANFrameFilterEx"
        else:
            add_can_frame_filter_function = "OCI_AddCANFrameFilter"
        self._oci_exec_check(add_can_frame_filter_function, False,
                             "Failed to add the frame filter",
                             self.oci_rx_queue, self.oci_filters, len(self.oci_filters))

    def _oci_remove_can_frame_filter(self):
        """
        Remove the previously configured CAN frame filters.
        """
        if self.oci_filters is None:
            return
        if self._check_boa_api_version(BOA_API_Version(1, 4, 0, 0)):
            remove_can_frame_filter_function = "OCI_RemoveCANFrameFilterEx"
        else:
            remove_can_frame_filter_function = "OCI_RemoveCANFrameFilter"
        self._oci_exec_check(remove_can_frame_filter_function, False,
                             "Failed to remove the frame filter",
                             self.oci_rx_queue, self.oci_filters, len(self.oci_filters))
        self.oci_filters = None

    def shutdown(self):
        """
        Shutdown can queues and controllers.
        """
        self._oci_destroy_can_controller()
        self.logger.info("Successfully shutdown")


class EtasBus(can.BusABC, EtasOCI):
    """
    The CAN Bus implemented for the BOA interface.

    Implements :meth:`can.BusABC._detect_available_configs`.
    """

    def __init__(self, channel=None, can_filters=None, bitrate=500000, **kwargs):
        """
        Whenever possible, names of the parameters mimic the ones of other existing interfaces of
        python-can in order to provide interoperability.

        :param Union[None,int,str] channel:
            None:
                Default value, will list all connected devices in an interactive prompt and asks for
                user input to specify the channel by index.
            int:
                It is the index of the channel of the CAN Device in the order they are connected
                (starts at 0, same index as in the interactive prompt).
            str:
                You can also specify a string, which is the name of the object to open. The format
                of the string is ``'ETAS://<bus type>/<device name>:<serial number>/CAN:<channel
                number>'`` (Example: ``'ETAS://USB/ES582.1:1234567/CAN:1'``). ``<device name>`` is
                printed on the front of the hardware and usually starts with "ES". ``<serial
                number>`` is usually found on the back of the device and ``<channel number>`` starts
                with 1.

                The output of :meth:`can.interfaces.etas.EtasCSI.enumerate_controllers` uses the
                same format and as such can be reused here.

                *Hint*: If ``<serial number>`` starts with ``0`` and it does not work, try to
                        remove that leading ``0``.

        :param Union[None,bool] use_hardware_filtering:
            ``False`` *(default)*: Use python-can filtering, ``True``: Use BOA filtering (see
            :attr:`~can.interfaces.etas.EtasBus.can_filters` below for details).

        :param Union[None,list] can_filters:
            Apply filtering to all messages received on this Bus.

            If :attr:`~can.interfaces.etas.EtasBus.use_hardware_filtering` is ``True`` *and* BOA API
            version is strictly below 1.4.0, only the ``can_id`` and ``can_mask`` filters are
            available (no ``extended`` filter).

            If :attr:`~can.interfaces.etas.EtasBus.use_hardware_filtering` is ``True`` *and* BOA API
            version is 1.4.0 or above, then below additional filters apply:

                - ``extended``:

                    - **not set**: matches both Standard Frame Format (SFF) and Extended Frame
                      Format (EFF).
                    - ``False``: matches only SFF.
                    - ``True``: matches only EFF.

                - ``remote_frame``:

                    - **not set**: matches both Remote Transmission Request (RTR) and normal
                      (non-RTR) frames.
                    - ``False``: matches only normal (non-RTR) frames.
                    - ``True``: matches only RTR frames.

                - ``fd``:

                    - **not set**: matches both standard and FD frames.
                    - ``False``: matches only standard (non-FD) frames.
                    - ``True``: matches only FD frames.

                - ``bitrate_switch``:

                    - **not set**: matches both FD frames with and without Bit Rate Switch (BRS).
                    - ``False``: matches only FD frames without BRS.
                    - ``True``: matches only the frames with BRS.

            **N.B.**: Some incompatibility might occur:

                - If ``fd`` is ``False`` and ``bitrate_switch`` is ``True``, then no frames will be
                  matched (non-FD frames can not have BRS).
                - If both ``fd`` and ``remote_frame`` are ``True``, then no frames will be matched
                  (FD frames can be RTR).

            Examples:

                Below example will only match frames that are 1/ EFF (non-SFF), 2/ either RTR or
                non-RTR (because ``remote_frame`` is not set), 3/ non-FD (and so, implicitly
                non-BRS) and 4/ for which the two last hexadecimal values of the CAN ID are 0x11.

                >>> [{"extended": True, "fd": False, "can_id": 0x11, "can_mask": 0xff}]

                Below example will only match frames that are 1/ either EFF or SFF (because
                ``extended`` is not set), 2/ non-RTR, 3/ FD **with** BRS (and 4/ all CAN-ID
                values are matched).

                >>> [{"remote_frame": False, "fd": True, "bitrate_switch": True, "can_id": 0x00,
                      "can_mask": 0x00}]

            For further details, please refer to :meth:`can.BusABC.set_filters`.

        :param Union[None,bool] receive_own_messages:
            If transmitted messages should also be received by this bus.

        :param Union[None,int] bitrate:
            Nominal Bitrate in bits/s.

            Not all Bitrates are supported. If the CAN controller can not be opened, try another
            bitrate.

        :param Union[None,bool] fd:
            This parameter corresponds to *canFDEnabled* in the BOA, it was renamed to *fd* for
            consistency with existing interfaces of python-can.

            ``False`` *(default)*: Standard CAN, ``True``: CAN-FD

        :param Union[None,int] data_bitrate:
            This parameter corresponds to *dataBitRate* in the BOA, it was renamed to *data_bitrate*
            for consistency with existing interfaces of python-can.

            The bitrate used for the data bytes of the CAN message. Only values up to
            *OCI_CANControllerCapabilities::canFDMaxDataRate* (see OCI-Documentation) can be used.

            Ignored if not using CAN-FD.

        :param Union[None,bool] dlc_is_len:
            The way python-can handles the DLC value is inaccurate. This Boolean allows to choose
            between two options:

                - ``False`` *(default)*: strictly follow ISO 11898-1 section 8.4.2.4 "DLC field"
                  (the DLC is a 4 bits value ranging between 0 and 15). Conversion between DLC and
                  length can be done using :meth:`~can.utils.can.util.dlc2len` and
                  :meth:`~can.utils.len2dlc`.
                - ``True``: use python-can convention: *"for data frames DLC represents the amount
                  of data contained in the message, for remote frames it represents the amount of
                  data being requested."*

        :param Union[None,int] selfReceptionMode:
            Specify whether the CAN controller / CAN controller firmware shall receive data sent
            through the same port. 0 *(default)*: self reception off, 1: self reception on.

        :param Union[None,tuple[int,int,int,int],can.interfaces.etas.BOA_API_Version] boa_api_version:
            The API version of BOA interface supported by the hardware.

            If the parameter is not specified the latest supported
            :attr:`~can.interfaces.etas.EtasBus.boa_api_version` will automatically be detected.

            Providing this parameter will allow to skip the automatic detection and allow a
            slightly faster start time. If start time is not an issue for you, leaving this
            parameter to ``None`` is recommended.

            To use CAN-FD it needs to be at least 1.3.0.0.

        All parameters listed below can be used to precisely set up the bittiming parameters. Unless
        you have specific needs, those parameters can usually be omitted.

        If those bittiming parameters are not set perfectly to match the bitrate, you will get a
        warning to inform you that the parameters have been automatically adjusted. This warning is
        silenced by default, to see it you need to set the logger level to, at least, ``INFO``.
        (See above for the command).

        :param Union[None,int] nom_tseg1:
            Time segment 1 for nominal bitrate: the number of time quanta from the end of the
            ``sync_seg`` to the :attr:`~can.interfaces.etas.OCI_CANConfiguration.samplePoint`.

            Gets ignored if :attr:`~can.interfaces.etas.EtasBus.nom_tseg2` is not specified.

        :param Union[None,int] nom_tseg2:
            Time segment 2 for nominal bitrate: the number of time quanta from the
            :attr:`~can.interfaces.etas.OCI_CANConfiguration.samplePoint` to the end of the bit.

            Gets ignored if :attr:`~can.interfaces.etas.EtasBus.nom_tseg1` is not specified.

        :param Union[None,int nom_sjw:
            Nominal Synchronization Jump Width: Length of the sync segment.

        :param Union[None,int] data_tseg1:
            Time segment 1 for data bitrate: the number of time quanta from the end of the
            ``sync_seg`` to the
            :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataSamplePoint`.

            Gets ignored if :attr:`~can.interfaces.etas.EtasBus.data_tseg2` is not specified or if
            not using CAN-FD.

            Ignored if not using CAN-FD.

        :param Union[None,int] data_tseg2:
            Time segment 2 for data bitrate: the number of time quanta from the
            :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataSamplePoint` to the end of the
            bit.

            Gets ignored if :attr:`~can.interfaces.etas.EtasBus.data_tseg1` is not specified or if
            not using CAN-FD.

        :param Union[None,int] data_sjw:
            The length of the data sync segment.

            Ignored if not using CAN-FD.

        :param Union[None,can.interfaces.etas.OCI_CANConfiguration] OCI_CANConfiguration:
            CAN parameters in ETAS BOA format.

            Some of the attributes of :class:`~can.interfaces.etas.OCI_CANConfiguration` are
            redundant with previous parameters. When a conflict occurs, the
            :class:`~can.interfaces.etas.OCI_CANConfiguration`'s attribute will be overwritten by
            the corresponding parameter according to below rules:

                - :attr:`~can.interfaces.etas.OCI_CANConfiguration.baudrate` will get ignored if
                  :attr:`~can.interfaces.etas.EtasBus.bitrate` is provided.

                - :attr:`~can.interfaces.etas.OCI_CANConfiguration.samplePoint` and
                  :attr:`~can.interfaces.etas.OCI_CANConfiguration.BTL_Cycles` will get ignored if
                  both :attr:`~can.interfaces.etas.EtasBus.nom_tseg1` and
                  :attr:`~can.interfaces.etas.EtasBus.nom_tseg2` are provided.

                - :attr:`~can.interfaces.etas.OCI_CANConfiguration.SJW` will get ignored if
                  :attr:`~can.interfaces.etas.EtasBus.nom_sjw` is provided.

                - :attr:`~can.interfaces.etas.OCI_CANConfiguration.canFDEnabled` will get ignored if
                  :attr:`~can.interfaces.etas.EtasBus.fd` is provided.

                - :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataBitRate` will get ignored
                  if :attr:`~can.interfaces.etas.EtasBus.data_bitrate` is provided.

                - :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataSamplePoint` and
                  :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataBTL_Cycles` will get
                  ignored if both :attr:`~can.interfaces.etas.EtasBus.data_tseg1` and
                  :attr:`~can.interfaces.etas.EtasBus.data_tseg2` are provided.

                - :attr:`~can.interfaces.etas.OCI_CANFDConfiguration.dataSJW` will get ignored if
                  :attr:`~can.interfaces.etas.EtasBus.data_sjw` is provided.


        :raise can.interfaces.etas.EtasError: If:

                - controller can't be created or opened.
                - Tx/Rx Queue can't be created.
                - frame filter can't be added.
                - Event filter can't be added.

        """
        EtasOCI.__init__(self, channel=channel)

        self.bus_state = BusState.STOPPED
        self.use_hardware_filtering = kwargs.get('use_hardware_filtering',
                                                 False)
        self.receive_own_messages = kwargs.get('receive_own_messages', False)
        self.dlc_is_len = kwargs.get('dlc_is_len', False)

        self._configure(bitrate, kwargs)
        self._start()

        # can.BusABC.__init__() calls _apply_filters(). As such, we need to instantiate the
        # attributes of self before calling that __init__.
        can.BusABC.__init__(self, channel=channel, bitrate=bitrate,
                            can_filters=can_filters, **kwargs)

    def _sanitize_boa_api_version(self, boa_api_version):
        sanitized_api_version = None
        if boa_api_version:
            try:
                sanitized_api_version = BOA_API_Version(*boa_api_version)
            except TypeError as error:
                self.logger.error("Could not convert \"%s\" to a BOA API version: %s. "
                                  "Ignoring parameter.", boa_api_version, error)
        return sanitized_api_version

    def _configure(self, bitrate, kwargs):
        """
        Create the configuration of the controller.

        :param Parameters:
            Passed from :meth:`~can.interfaces.etas.EtasBus` and documented there.
        """
        default_can_conf = OCI_CANConfiguration(
            baudrate=500000,
            samplePoint=75,
            samplesPerBit=OCI_CAN_THREE_SAMPLES_PER_BIT,
            BTL_Cycles=20,
            SJW=4,
            syncEdge=OCI_CAN_SINGLE_SYNC_EDGE,
            physicalMedia=OCI_CAN_MEDIA_HIGH_SPEED,
            selfReceptionMode=OCI_SELF_RECEPTION_OFF,
            busParticipationMode=OCI_BUSMODE_ACTIVE,
            canFDEnabled=int(False),
            canFDConfig=OCI_CANFDConfiguration(
                dataBitRate=2000000,
                dataSamplePoint=60,
                dataBTL_Cycles=12,
                dataSJW=3,
                flags=0,
                txSecondarySamplePointOffset=0,
                canFdRxConfig=OCI_CANFDRxConfig(OCI_CAN_RXMODE_CAN_FRAMES_USING_CAN_MESSAGE,
                                                OCI_CANFDRXMODE_CANFD_FRAMES_USING_CANFD_MESSAGE),
                canFdTxConfig=OCI_CANFDTX_USE_CAN_AND_CANFD_FRAMES,
                txSecondarySamplePointFilterWindow=0,
                reserved=0
            )
        )

        sync_seg = 1

        self._oci_create_can_controller(
            self._sanitize_boa_api_version(kwargs.get('boa_api_version', None))
        )
        self._oci_get_timer_capabilities()
        self._oci_get_controller_capabilities()
        if self._oci_get_can_configuration():
            self.logger.warning("The controller has already been configured by another program. "
                                "Ignoring provided configuration and continuing with current "
                                "configuration instead.")
            self.logger.info("Please use print_controller_configuration() method to see current "
                             "configuration.")
            return

        can_conf = kwargs.get('OCI_CANConfiguration', default_can_conf)

        can_conf.baudrate = bitrate if bitrate is not None else can_conf.baudrate
        can_conf.SJW = kwargs.get('nom_sjw', can_conf.SJW)
        can_conf.selfReceptionMode = (OCI_SELF_RECEPTION_ON if self.receive_own_messages
                                      else OCI_SELF_RECEPTION_OFF)
        can_conf.canFDEnabled = kwargs.get('fd', can_conf.canFDEnabled)
        if kwargs.get('nom_tseg1') is not None and kwargs.get('nom_tseg2') is not None:
            can_conf.BTL_Cycles = sync_seg + kwargs.get('nom_tseg1') + kwargs.get('nom_tseg2')
            can_conf.samplePoint = int((sync_seg + kwargs.get('nom_tseg1')) /
                                       can_conf.BTL_Cycles * 100)

        if can_conf.canFDEnabled:
            can_fd_conf = can_conf.canFDConfig

            if not self.oci_can_controller_capabilities.is_fd_capable:
                raise EtasError("Controller does not support CAN FD.")

            can_fd_conf.data_bitrate = kwargs.get('data_bitrate', can_fd_conf.dataBitRate)
            can_fd_conf.dataSJW = kwargs.get('data_sjw', can_fd_conf.dataSJW)
            if kwargs.get('data_tseg1') is not None and kwargs.get('data_tseg2') is not None:
                can_fd_conf.dataBTL_Cycles = (sync_seg + kwargs.get('data_tseg1') +
                                              kwargs.get('data_tseg2'))
                can_fd_conf.dataSamplePoint = int((sync_seg + kwargs.get('data_tseg1')) /
                                                  can_fd_conf.dataBTL_Cycles * 100)

        else:
            can_fd_conf = OCI_CANFDConfiguration()

        self.oci_can_configuration = can_conf

    def _start(self):
        self._oci_create_can_controller()
        self._oci_open_can_controller()
        self._oci_create_can_tx_queue()
        self._oci_create_can_rx_queue(
            event_call_back=OCI_CANRxCallbackSingleMsg(function=event_callback,
                                                       userData=ct.pointer(ct.py_object(self))),
            receive_own_messages=self.receive_own_messages
        )
        self._oci_add_can_bus_event_filter()

        ## Errorframes are caught by _recv_internal, uncomment this line to trigger the callback
        ## function each time an error is received
        #self._oci_add_can_bus_error_frame_filter()

        self.bus_state = BusState.ERROR_ACTIVE
        self.logger.info("Channel becomes ready.")

    def _recv_internal(self, timeout):
        """
        Read a message from a Etas bus.

        :param float timeout:
            Max time to wait in seconds or None if infinite, should not be negative.

        :rtype: tuple[Union[can.interfaces.etas.EtasMessage,None],bool]
        :return:
            1.  a message that was read or None on timeout.
            2.  a bool that is ``True`` if message filtering has already
                been done and else False.
        """
        rx_message, count = self._oci_read_can_data(timeout)
        if count == 0:
            return None, self.use_hardware_filtering

        rx_msg = rx_message.data.rxMessage

        flags = (int)(rx_msg.flags)
        is_remote_frame = flags & OCI_CAN_MSG_FLAG['remote_frame']['value'] != 0
        is_error_frame = rx_message.type == OCI_CAN_ERROR_FRAME.value
        is_fd = flags & OCI_CAN_MSG_FLAG['fd']['value'] != 0
        if is_fd:
            # do a double conversation to sanitize the length for fd, use dlc for normal CAN
            dlc = can.util.len2dlc(rx_msg.size)
            sanitized_len = can.util.dlc2len(dlc)
            if sanitized_len != rx_msg.size:
                self.logger.error("Rx message length: %d does not correspond to a valid DLC. "
                                  "It was sanitized to %d.", rx_msg.size, sanitized_len)
        else:
            sanitized_len = min(8, rx_msg.size)
            dlc = rx_msg.size

        if is_remote_frame or is_error_frame:
            data = None
        else:
            data = rx_msg.data[0:sanitized_len]

        msg = EtasMessage(
            # Timestamp is from the time the can device is connected to the PC
            # If two devices are connected, their time is not synced
            timestamp=self.tick_to_time(rx_msg.timeStamp),
            arbitration_id=rx_msg.frameID,
            is_extended_id=flags & OCI_CAN_MSG_FLAG['extended']['value'] != 0,
            is_remote_frame=is_remote_frame,
            is_error_frame=is_error_frame,
            is_fd=is_fd,
            bitrate_switch=flags & OCI_CAN_MSG_FLAG['bitrate_switch']['value'] != 0
            if is_fd else 0,
            error_state_indicator=flags & OCI_CAN_MSG_FLAG['error_state_indicator']['value'] != 0
            if is_fd else 0,
            # File ``doc/message.rst`` states that "[DLC] purpose varies depending on the frame
            # type - for data frames it represents the amount of data contained in the message,
            # in remote frames it represents the amount of data being requested."
            # User can choose between the ISO 11898-1 standard and the python-can convention.
            dlc=sanitized_len if self.dlc_is_len else dlc,
            data=data,
            is_self_reception=flags & OCI_CAN_MSG_FLAG['selfreception']['value'] != 0,
            dlc_is_len=self.dlc_is_len
        )

        if is_error_frame:
            self.logger.info("Timestamp: %f, BUS ERROR FRAME: %s, FrameID: %d", msg.timestamp,
                             OCI_CAN_ERR_TYPES[rx_message.data.errorFrameMessage.type]
                             ['description'],
                             rx_message.data.errorFrameMessage.frameID)

        self.logger.log(logging.DEBUG - 1, "Rx message. %s", msg)
        return msg, self.use_hardware_filtering

    def send(self, msg, timeout=None):
        """
        Send a Message over to the BOA interface.

        If the length of the message doesn't correspond to a valid DLC, the end of the message gets
        padded with 0x00 until it does.

        :param can.Message msg:
            Message to send

        :raise can.interfaces.etas.EtasError: If:

                - writing to transmit buffer fails.
                - remote frame is set to ``True`` for an FD message or if the hardware doesn't
                  support it.

        """
        arb_id = msg.arbitration_id
        can_message_data = OCI_CANMessageDataEx()

        if msg.is_fd and not self.oci_can_configuration.canFDEnabled:
            self.logger.error("Message has the is_fd flag set to True but CAN-FD has not been "
                              "enabled on the controller! Removing FD flag.")
            msg.is_fd = False

        dlc, sanitized_len, data = self._sanitize_can_dlc_and_data(msg)
        oci_flags = self._oci_can_msg_flag(msg)

        if msg.is_fd:
            tx_type = OCI_CANFDTX_MESSAGE
            can_message_data = OCI_CANMessageDataEx(
                canFDTxMessage=OCI_CANFDTxMessage(
                    frameID=arb_id,
                    flags=oci_flags,
                    size=sanitized_len,
                    data=CanDataFD(*data[0:64])
                )
            )
        else:
            tx_type = OCI_CAN_TX_MESSAGE
            can_message_data = OCI_CANMessageDataEx(
                txMessage=OCI_CANTxMessage(
                    frameID=arb_id,
                    flags=oci_flags,
                    dlc=dlc,
                    data=CanData(*data[0:8])
                )
            )

        self._oci_write_can_data(OCI_CANMessageEx(tx_type, 0, can_message_data))
        self.logger.log(logging.DEBUG - 1, "Tx message. %s", msg)

    def _sanitize_can_dlc_and_data(self, msg):
        """
        Return a sanitized value of the CAN DLC and the Length. Truncate or pad the CAN message
        data accordingly.

        :param can.Message msg:
            CAN message.

        :rtype: tuple[int, int, list[int]]
        :return:
            1.  Sanitized DLC value.
            2.  Sanitized messages length.
            3.  Truncated or pad data.
        """
        raw_len = len(msg.data)
        #Do a double conversation to sanitize the length.
        sanitized_len = can.util.dlc2len(can.util.len2dlc(raw_len))

        if self.dlc_is_len:
            dlc = can.util.len2dlc(msg.dlc)
        elif msg.dlc > 8 and msg.dlc == raw_len:
            # Provided DLC value seems to be the length, not the actual DLC!
            dlc = can.util.len2dlc(msg.dlc)
        elif msg.dlc > 15:
            dlc = 15
            self.logger.info("DLC value of %d is out of range (maximum value is 15 because DLC is "
                             "represented on 4 bits). DLC was set to %d.", msg.dlc, dlc)
        else:
            dlc = msg.dlc

        #Do a local copy in order to not tamper user data
        data = msg.data.copy()
        # pad message so that sanitized_len corresponds to the next valid dlc
        data.extend([0x00] * (64 - len(data)))
        if raw_len != sanitized_len:
            self.logger.info("Tx message length: %d does not correspond to a valid DLC. It was "
                             "sanitized to %d and data were padded with %d zero bytes.",
                             raw_len, sanitized_len, sanitized_len - raw_len)
        if ((msg.is_fd or sanitized_len < 8) and
                (dlc > can.util.len2dlc(sanitized_len))):
            new_sanitized_len = can.util.dlc2len(dlc) if msg.is_fd else min(can.util.dlc2len(dlc),
                                                                            8)
            self.logger.info("Tx message length is %d but requested DLC is %d. "
                             "Data were padded with %d zero bytes.",
                             sanitized_len, dlc, new_sanitized_len - sanitized_len)
            sanitized_len = new_sanitized_len
        elif dlc < can.util.len2dlc(sanitized_len):
            self.logger.info("Tx message length is %d but requested DLC is %d. "
                             "Last %d bytes of Data were removed.",
                             sanitized_len, dlc, sanitized_len - can.util.dlc2len(dlc))
            sanitized_len = can.util.dlc2len(dlc)

        if not msg.is_fd:
            if sanitized_len > 8:
                self.logger.info("Tx message length: %d is out of range for Standard CAN. "
                                 "Data were truncated to 8 bytes but DLC value was kept to %d.",
                                 raw_len, dlc)
                sanitized_len = 8
            if msg.is_remote_frame:
                if sanitized_len > 0:
                    self.logger.info("Remote Transmission Request frames (RTR) have no payload. "
                                     "Message Data will be ignored.")
                    sanitized_len = 0

        return dlc, sanitized_len, data

    def _oci_can_msg_flag(self, msg):
        """
        Calculate the OCI CAN flags of a given CAN message. Ignore unsupported flags (either
        because of incorrect flag combination or because not supported by the hardware).

        :param can.Message msg:
            CAN message.

        :rtype: int
        :return: the OCI flags.
        """
        oci_flags = 0

        if msg.is_extended_id:
            oci_flags |= OCI_CAN_MSG_FLAG['extended']['value']
        if msg.is_fd:
            oci_flags |= OCI_CAN_MSG_FLAG['fd']['value']
            if msg.is_remote_frame:
                self.logger.error("Message has both the is_remote_frame and is_fd flags set to "
                                  "True. This combination is impossible! Removing Remote Frame "
                                  "flag.")
                msg.is_remote_frame = False
            if msg.bitrate_switch:
                oci_flags |= OCI_CAN_MSG_FLAG['bitrate_switch']['value']
            if msg.error_state_indicator:
                oci_flags |= OCI_CAN_MSG_FLAG['error_state_indicator']['value']
        else:
            if msg.is_remote_frame:
                oci_flags |= OCI_CAN_MSG_FLAG['remote_frame']['value']
            if msg.bitrate_switch:
                self.logger.error("Message has the bitrate_switch flag set to True but is not a "
                                  "CAN-FD message! Removing the Bitrate Switch flag.")
                msg.bitrate_switch = False
            if msg.error_state_indicator:
                self.logger.error("Message has the error_state_indicator flag set to True but is "
                                  "not a CAN-FD message! Removing the Error State Indicator flag.")
                msg.error_state_indicator = False

        unsupported_flags = oci_flags & ~self.oci_can_controller_capabilities.messageFlags
        if unsupported_flags:
            for _oci_can_flag_key, oci_can_flag in OCI_CAN_MSG_FLAG.items():
                if unsupported_flags & oci_can_flag['value']:
                    self.logger.error("%s flag (%s) is not supported on this Hardware!",
                                      oci_can_flag['name'],
                                      oci_can_flag['description'])
            oci_flags &= ~unsupported_flags
            self.logger.warning("Removed unsupported flags.")

        return oci_flags

    def _apply_filters(self, filters=None):
        """
        Hook for applying the filters to the OCI.

        Supports hardware filtering, if self.use_hardware_filtering is explicitly set to ``True``,
        else the Python-can filter will be used per default.

        :param Iterator[dict] filters:
            Filters to be applied. See :meth:`~can.BusABC.set_filters` for details.
        """
        self._oci_remove_can_frame_filter()

        empty_filters = (not self.use_hardware_filtering) or (filters is None)
        if empty_filters:
            # Have to apply a whitelist filter since BOA blacklists everything by default
            filters = [{"can_id": 0x00, "can_mask": 0x00}]


        if self._check_boa_api_version(BOA_API_Version(1, 4, 0, 0)):
            self._apply_extended_filters(filters)
        else:
            self._apply_legacy_filters(filters)

        self._oci_add_can_frame_filter()

        if not empty_filters:
            count = len(filters)
            self.logger.debug("Applied %d hardware filter%s.", count, "s" if count > 1 else "")

    def _apply_legacy_filters(self, filters):
        """
        Legacy filters (up to BOA API version 1.3.0.0).

        :param Iterator[dict] filters:
            Filters to be applied. See :meth:`~can.BusABC.set_filters` for details.
        """
        self.oci_filters = (OCI_CANRxFilter * len(filters))()

        for oci_filter, user_filter in zip(self.oci_filters, filters):
            if user_filter.get('extended', False):
                self.logger.warning("Extended Filter only works in BOA API version 1.4.0.0 "
                                    "or higher. Extended flag will be ignored.")
            oci_filter.frameIDValue = user_filter['can_id']
            oci_filter.frameIDMask = user_filter['can_mask'] & 0x1FFFFFFF

    def _apply_extended_filters(self, filters):
        """
        Extended filters (BOA API version 1.4.0.0 or greater).

        :param Iterator[dict] filters:
            Filters to be applied. See :meth:`~can.BusABC.set_filters` for details.
        """
        self.oci_filters = (ct.POINTER(OCI_CANRxFilterEx) * len(filters))()

        for ptr_oci_filter, user_filter in zip(self.oci_filters, filters):
            flags_value = 0
            flags_mask = 0
            for oci_can_flag_key, oci_can_flag in OCI_CAN_MSG_FLAG.items():
                if not self.oci_can_controller_capabilities.messageFlags & oci_can_flag['value']:
                    continue
                if oci_can_flag_key == 'selfreception':
                    if not self.receive_own_messages:
                        flags_mask |= OCI_CAN_MSG_FLAG['selfreception']['value']
                else:
                    if oci_can_flag_key in user_filter:
                        flags_mask |= oci_can_flag['value']
                        if user_filter[oci_can_flag_key]:
                            flags_value |= oci_can_flag['value']

            ptr_oci_filter.contents = OCI_CANRxFilterEx(
                frameIDValue=user_filter['can_id'],
                frameIDMask=user_filter['can_mask'] & 0x1FFFFFFF,
                tag=user_filter['can_id'],
                flagsValue=ct.c_uint16(flags_value),
                flagsMask=ct.c_uint16(flags_mask)
            )

    @property
    def controller_name(self):
        """
        :getter: The name of the CAN controller (example: ES582.1).

        :type: str
        """
        return self.channel_info.split('/')[3].split(':')[0]

    @property
    def state(self):
        """
        The state of the CAN controller.

        :getter: Return the current state.

        :setter: Take proper actions if needed (restart/shutdown) and sets the state of the CAN
            controller.

        :raise can.interfaces.etas.EtasError:
            If the requested ``new_state`` is neither
            :attr:`~can.interfaces.etas.BusState.ERROR_ACTIVE` nor
            :attr:`~can.interfaces.etas.BusState.STOPPED` (and is different than the current state)

        :type: can.interfaces.etas.BusState
        """
        return self.bus_state

    @state.setter
    def state(self, new_state):
        current_state = self.bus_state

        if current_state == new_state:
            self.logger.info("Already in '%s', doing nothing.", new_state)
            return

        self.logger.info("Switching from %s to %s.",
                         current_state, new_state)
        if new_state == BusState.ERROR_ACTIVE:
            if current_state != BusState.STOPPED:
                self.reset()
                return
            self._start()
            self._apply_filters(self.filters)
            return
        if new_state == BusState.STOPPED:
            self._oci_close_can_controller()
            return

        raise EtasError("Operation not supported: can not switch from {} to {}."
                        .format(current_state, new_state))

    def flush_tx_buffer(self):
        """
        Discard every message that may be queued in the output buffer.

        :raise can.interfaces.etas.EtasError:
            If the destruction or following creation of the tx queue failed.
        """
        self._oci_destroy_can_tx_queue()
        self._oci_create_can_tx_queue()

        self.logger.info("Flushed the tx buffer")

    def reset(self):
        """
        Fully resets the CAN controller by destroying and recreating its instance.
        """
        self.logger.info("Resetting")
        self._oci_close_can_controller()
        self._start()
        self._apply_filters(self.filters)

    def shutdown(self):
        """
        Shutdown can queues and controllers.
        """
        EtasOCI.shutdown(self)
        self.bus_state = BusState.STOPPED

    @staticmethod
    def _detect_available_configs():
        return [{'interface': 'etas', 'channel': channel}
                for channel in EtasCSI.enumerate_controllers()]

    def print_controller_capabilities(self):
        """
        Print out controller capabilities.

        For the exact meaning of the values, refer to the BOA documentation.
        """
        print(self, "controller capabilities:")
        print(self.oci_can_controller_capabilities)

    def get_controller_capabilities(self):
        """
        Get controller capabilities as dictionary.

        For the exact meaning of the values, refer to the BOA documentation.

        :rtype: dict[str, int]
        :return: controller_capabilities.
        """
        return self.oci_can_controller_capabilities.get_controller_capabilities()

    def print_controller_configuration(self):
        """
        Print out controller configuration.

        For the exact meaning of the values, refer to the BOA documentation.
        """
        print(self, "controller configuration:")
        print(self.oci_can_configuration)

    def get_controller_configuration(self):
        """
        Get controller configuration as dictionary.

        For the exact meaning of the values, refer to the BOA documentation.

        :rtype: dict[str, int]
        :return: controller_configuration.
        """
        return self.oci_can_configuration.get_controller_configuration()

class EtasError(can.CanError):
    """
    A generic error on an Etas bus.
    """

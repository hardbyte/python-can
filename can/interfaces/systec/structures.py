# coding: utf-8

from ctypes import Structure, WINFUNCTYPE, POINTER, sizeof, c_ubyte as BYTE
from ctypes.wintypes import WORD, DWORD, BOOL, LPVOID

from .constants import MsgFrameFormat


class CanMsg(Structure):
    """
    Structure of a CAN message.

    .. seealso::

       :meth:`UcanServer.read_can_msg`

       :meth:`UcanServer.write_can_msg`

       :meth:`UcanServer.define_cyclic_can_msg`

       :meth:`UcanServer.read_cyclic_can_msg`
    """
    _pack_ = 1
    _fields_ = [
        ("m_dwID", DWORD),  # CAN Identifier
        ("m_bFF", BYTE),  # CAN Frame Format (see enum :class:`MsgFrameFormat`)
        ("m_bDLC", BYTE),  # CAN Data Length Code
        ("m_bData", BYTE * 8),  # CAN Data (array of 8 bytes)
        ("m_dwTime", DWORD,)  # Receive time stamp in ms (for transmit messages no meaning)
    ]

    def __init__(self, id=0, frame_format=MsgFrameFormat.MSG_FF_STD, data=[]):
        super(CanMsg, self).__init__(id, frame_format, len(data), (BYTE * 8)(*data), 0)

    @property
    def id(self): return self.m_dwID

    @id.setter
    def id(self, id): self.m_dwID = id

    @property
    def frame_format(self): return self.m_bFF

    @frame_format.setter
    def frame_format(self, frame_format): self.m_bFF = frame_format

    @property
    def data(self): return self.m_bData[:self.m_bDLC]

    @data.setter
    def data(self, data):
        self.m_bDLC = len(data)
        self.m_bData((BYTE * 8)(*data))

    @property
    def time(self): return self.m_dwTime


class Status(Structure):
    """
    Structure with the error status of CAN and USB.
    Use this structure with the method :meth:`UcanServer.get_status`

    .. seealso::

       :meth:`UcanServer.get_status`

       :meth:`UcanServer.get_can_status_message`
    """
    _pack_ = 1
    _fields_ = [
        ("m_wCanStatus", WORD),  # CAN error status (see enum :class:`CanStatus`)
        ("m_wUsbStatus", WORD),  # USB error status (see enum :class:`UsbStatus`)
    ]

    @property
    def can_status(self): return self.m_wCanStatus

    @property
    def usb_status(self): return self.m_wUsbStatus


class InitCanParam(Structure):
    """
    Structure including initialisation parameters used internally in :meth:`UcanServer.init_can`.

    .. note:: This structure is only used internally.
    """
    _pack_ = 1
    _fields_ = [
        ("m_dwSize", DWORD),  # size of this structure (only used internally)
        ("m_bMode", BYTE),  # selects the mode of CAN controller (see enum :class:`Mode`)
        # Baudrate Registers for GW-001 or GW-002
        ("m_bBTR0", BYTE),  # Bus Timing Register 0 (see enum :class:`Baudrate`)
        ("m_bBTR1", BYTE),  # Bus Timing Register 1 (see enum :class:`Baudrate`)
        ("m_bOCR", BYTE),  # Output Control Register (see enum :class:`OutputControl`)
        ("m_dwAMR", DWORD),  # Acceptance Mask Register (see method :meth:`UcanServer.set_acceptance`)
        ("m_dwACR", DWORD),  # Acceptance Code Register (see method :meth:`UcanServer.set_acceptance`)
        ("m_dwBaudrate", DWORD),  # Baudrate Register for all systec USB-CANmoduls
                                  # (see enum :class:`BaudrateEx`)
        ("m_wNrOfRxBufferEntries", WORD),  # number of receive buffer entries (default is 4096)
        ("m_wNrOfTxBufferEntries", WORD),  # number of transmit buffer entries (default is 4096)
    ]

    def __init__(self, mode, BTR, OCR, AMR, ACR, baudrate, rx_buffer_entries, tx_buffer_entries):
        super(InitCanParam, self).__init__(sizeof(InitCanParam), mode, BTR >> 8, BTR, OCR, AMR, ACR,
                                           baudrate, rx_buffer_entries, tx_buffer_entries)

    @property
    def mode(self): return self.m_bMode

    @mode.setter
    def mode(self, mode): self.m_bMode = mode

    @property
    def BTR(self): return self.m_bBTR0 << 8 | self.m_bBTR1

    @BTR.setter
    def BTR(self, BTR): self.m_bBTR0, self.m_bBTR1 = BTR >> 8, BTR

    @property
    def OCR(self): return self.m_bOCR

    @OCR.setter
    def OCR(self, OCR): self.m_bOCR = OCR

    @property
    def baudrate(self): return self.m_dwBaudrate

    @baudrate.setter
    def baudrate(self, baudrate): self.m_dwBaudrate = baudrate

    @property
    def rx_buffer_entries(self): return self.m_wNrOfRxBufferEntries

    @rx_buffer_entries.setter
    def rx_buffer_entries(self, rx_buffer_entries): self.m_wNrOfRxBufferEntries = rx_buffer_entries

    @property
    def tx_buffer_entries(self): return self.m_wNrOfTxBufferEntries

    @rx_buffer_entries.setter
    def tx_buffer_entries(self, tx_buffer_entries): self.m_wNrOfTxBufferEntries = tx_buffer_entries


class Handle(BYTE):
    pass


class HardwareInfoEx(Structure):
    """
    Structure including hardware information about the USB-CANmodul.
    This structure is used with the method :meth:`UcanServer.get_hardware_info`.

    .. seealso:: :meth:`UcanServer.get_hardware_info`
    """
    _pack_ = 1
    _fields_ = [
        ("m_dwSize", DWORD),  # size of this structure (only used internally)
        ("m_UcanHandle", Handle),  # USB-CAN-Handle assigned by the DLL
        ("m_bDeviceNr", BYTE),  # device number of the USB-CANmodul
        ("m_dwSerialNr", DWORD),  # serial number from USB-CANmodul
        ("m_dwFwVersionEx", DWORD),  # version of firmware
        ("m_dwProductCode", DWORD),  # product code (see enum :class:`ProductCode`)
        # unique ID (available since V5.01) !!! m_dwSize must be >= HWINFO_SIZE_V2
        ("m_dwUniqueId0", DWORD),
        ("m_dwUniqueId1", DWORD),
        ("m_dwUniqueId2", DWORD),
        ("m_dwUniqueId3", DWORD),
        ("m_dwFlags", DWORD),  # additional flags
    ]

    def __init__(self):
        super(HardwareInfoEx, self).__init__(sizeof(HardwareInfoEx))

    @property
    def device_number(self): return self.m_bDeviceNr

    @property
    def serial(self): return self.m_dwSerialNr

    @property
    def fw_version(self): return self.m_dwFwVersionEx

    @property
    def product_code(self): return self.m_dwProductCode

    @property
    def unique_id(self): return self.m_dwUniqueId0, self.m_dwUniqueId1, self.m_dwUniqueId2, self.m_dwUniqueId3

    @property
    def flags(self): return self.m_dwFlags


# void PUBLIC UcanCallbackFktEx (Handle UcanHandle_p, DWORD dwEvent_p,
#                                BYTE bChannel_p, void* pArg_p);
CallbackFktEx = WINFUNCTYPE(None, Handle, DWORD, BYTE, LPVOID)


class HardwareInitInfo(Structure):
    """
    Structure including information about the enumeration of USB-CANmoduls.

    .. seealso:: :meth:`UcanServer.enumerate_hardware`

    .. note:: This structure is only used internally.
    """
    _pack_ = 1
    _fields_ = [
        ("m_dwSize", DWORD),  # size of this structure
        ("m_fDoInitialize", BOOL),  # specifies if the found module should be initialized by the DLL
        ("m_pUcanHandle", Handle),  # pointer to variable receiving the USB-CAN-Handle
        ("m_fpCallbackFktEx", CallbackFktEx),  # pointer to callback function
        ("m_pCallbackArg", LPVOID),  # pointer to user defined parameter for callback function
        ("m_fTryNext", BOOL),  # specifies if a further module should be found
    ]


class ChannelInfo(Structure):
    """
    Structure including CAN channel information.
    This structure is used with the method :meth:`UcanServer.get_hardware_info`.

    .. seealso:: :meth:`UcanServer.get_hardware_info`
    """
    _pack_ = 1
    _fields_ = [
        ("m_dwSize", DWORD),  # size of this structure
        ("m_bMode", BYTE),  # operation mode of CAN controller (see enum :class:`Mode`)
        ("m_bBTR0", BYTE),  # Bus Timing Register 0 (see enum :class:`Baudrate`)
        ("m_bBTR1", BYTE),  # Bus Timing Register 1 (see enum :class:`Baudrate`)
        ("m_bOCR", BYTE),  # Output Control Register (see enum :class:`OutputControl`)
        ("m_dwAMR", DWORD),  # Acceptance Mask Register (see method :meth:`UcanServer.set_acceptance`)
        ("m_dwACR", DWORD),  # Acceptance Code Register (see method :meth:`UcanServer.set_acceptance`)
        ("m_dwBaudrate", DWORD),  # Baudrate Register for all systec USB-CANmoduls
                                  # (see enum :class:`BaudrateEx`)
        ("m_fCanIsInit", BOOL),  # True if the CAN interface is initialized, otherwise false
        ("m_wCanStatus", WORD),  # CAN status (same as received by method :meth:`UcanServer.get_status`)
    ]

    def __init__(self):
        super(ChannelInfo, self).__init__(sizeof(ChannelInfo))

    @property
    def mode(self): return self.m_bMode

    @property
    def BTR(self): return self.m_bBTR0 << 8 | self.m_bBTR1

    @property
    def OCR(self): return self.m_bOCR

    @property
    def AMR(self): return self.m_dwAMR

    @property
    def ACR(self): return self.m_dwACR

    @property
    def baudrate(self): return self.m_dwBaudrate

    @property
    def can_is_init(self): return self.m_fCanIsInit

    @property
    def can_status(self): return self.m_wCanStatus


class MsgCountInfo(Structure):
    """
    Structure including the number of sent and received CAN messages.
    This structure is used with the method :meth:`UcanServer.get_msg_count_info`.

    .. seealso:: :meth:`UcanServer.get_msg_count_info`

    .. note:: This structure is only used internally.
    """
    _fields_ = [
        ("m_wSentMsgCount", WORD),  # number of sent CAN messages
        ("m_wRecvdMsgCount", WORD),  # number of received CAN messages
    ]

    @property
    def sent_msg_count(self): return self.m_wSentMsgCount

    @property
    def recv_msg_count(self): return self.m_wRecvdMsgCount


# void (PUBLIC *ConnectControlFktEx) (DWORD dwEvent_p, DWORD dwParam_p, void* pArg_p);
ConnectControlFktEx = WINFUNCTYPE(None, DWORD, DWORD, LPVOID)

# typedef void (PUBLIC *EnumCallback) (DWORD dwIndex_p, BOOL fIsUsed_p,
#    HardwareInfoEx* pHwInfoEx_p, HardwareInitInfo* pInitInfo_p, void* pArg_p);
EnumCallback = WINFUNCTYPE(None, DWORD, BOOL, POINTER(HardwareInfoEx), POINTER(HardwareInitInfo), LPVOID)

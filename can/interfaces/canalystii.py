from ctypes import *
import logging
import platform
from can import BusABC, Message
from typing import Optional, Dict

logger = logging.getLogger(__name__)

VCI_USBCAN2 = 4
STATUS_OK = 0x01
STATUS_ERR = 0x00

TIMING_DICT = {
    5000: (0xBF, 0xFF),
    10000: (0x31, 0x1C),
    20000: (0x18, 0x1C),
    33330: (0x09, 0x6F),
    40000: (0x87, 0xFF),
    50000: (0x09, 0x1C),
    66660: (0x04, 0x6F),
    80000: (0x83, 0xFF),
    83330: (0x03, 0x6F),
    100000: (0x04, 0x1C),
    125000: (0x03, 0x1C),
    200000: (0x81, 0xFA),
    250000: (0x01, 0x1C),
    400000: (0x80, 0xFA),
    500000: (0x00, 0x1C),
    666000: (0x80, 0xB6),
    800000: (0x00, 0x16),
    1000000: (0x00, 0x14),
}

try:
    if platform.system() == "Windows":
        CANalystII = WinDLL("./ControlCAN.dll")
    else:
        CANalystII = CDLL("./libcontrolcan.so")
    logger.info("Loaded CANalystII library")
except OSError as e:
    CANalystII = None
    logger.info("Cannot load CANalystII library")


class VCI_INIT_CONFIG(Structure):
    _fields_ = [
        ("AccCode", c_ulong),
        ("AccMask", c_ulong),
        ("Reserved", c_ulong),
        ("Filter", c_ubyte),
        ("Timing0", c_ubyte),
        ("Timing1", c_ubyte),
        ("Mode", c_ubyte),
    ]


class VCI_CAN_OBJ(Structure):
    _fields_ = [
        ("ID", c_uint),
        ("TimeStamp", c_int),
        ("TimeFlag", c_byte),
        ("SendType", c_byte),
        ("RemoteFlag", c_byte),
        ("ExternFlag", c_byte),
        ("DataLen", c_byte),
        ("Data", c_byte * 8),
        ("Reserved", c_byte * 3),
    ]


class VCI_BOARD_INFO(Structure):
    _fields_ = [
        ('hw_Version', c_ushort),
        ('fw_Version', c_ushort),
        ('dr_Version', c_ushort),
        ('in_Version', c_ushort),
        ('irq_Num', c_ushort),
        ('can_Num', c_byte),
        ('str_Serial_Num', c_char * 20),
        ('str_hw_Type', c_char * 40),
        ('Reserved', c_ushort * 4)
    ]


_in_use = {}


class CANalystIIBus(BusABC):
    def __init__(
        self,
        channel: int,
        device: int = 0,
        bitrate: Optional[int] = None,
        Timing0: Optional[int] = None,
        Timing1: Optional[int] = None,
        can_filters=None,
        **kwargs,
    ):
        """
        CANalystII Interface

        :param channel: channel number to use
        :type channel: int

        :param device: device index. If there is more then one adapter the index number will be
            incremented by one for each additional adapter.
        :type device: int

        :param bitrate: CAN network bandwidth (bits/s).
        :type bitrate: int, optional

        :param Timing0: customize the timing register if bitrate is not specified.
        :type Timing0: int, optional

        :param Timing1: customize the timing register if bitrate is not specified.
        :type Timing1: int, optional

        :param can_filters: filters for packet
        """

        if CANalystII is None:
            raise RuntimeError('CANalystII library failed to load.')

        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

        self.channel = channel
        self.device = device
        self.channel_info = "CANalyst-II: device {}, channel {}".format(
            self.device,
            self.channel
        )

        if bitrate is not None:
            if bitrate in TIMING_DICT:
                Timing0, Timing1 = TIMING_DICT[bitrate]
            else:
                raise ValueError("Bitrate is not supported ({0})".format(bitrate))

        if None in (Timing0, Timing1):
            raise ValueError("Timing registers are not set")

        if device not in _in_use:
            try:
                CANalystII.VCI_UsbDeviceReset(VCI_USBCAN2, self.device, 0)
            except:
                pass

            b_info = VCI_BOARD_INFO()
            if CANalystII.VCI_ReadBoardInfo(VCI_USBCAN2, device, byref(b_info)) == STATUS_ERR:
                logger.error("VCI_ReadBoardInfo Error")

            self._b_info = dict(
                hardware_version=b_info.hw_Version,
                firmware_version=b_info.fw_Version,
                driver_version=b_info.dr_Version,
                library_version=b_info.in_Version,
                irq=b_info.irq_Num,
                num_can_interfaces=b_info.can_Num,
                serial_number=str(b_info.str_Serial_Num, encoding='ascii'),
                hardware_type=str(b_info.str_hw_Type, encoding='ascii')
            )

            if CANalystII.VCI_OpenDevice(VCI_USBCAN2, self.device, 0) == STATUS_ERR:
                raise ValueError('Unable to open interface, the device number supplied may be incorrect')

            _in_use[device] = []
        else:
            for cb in _in_use[device]:
                if cb.channel == channel:
                    raise ValueError(
                        'Channel {0} already in use for device {1}'.format(
                            channel,
                            device
                        )
                    )
            self._b_info = _in_use[device][0].board_info

        _in_use[device] += [self]

        self.init_config = VCI_INIT_CONFIG(0, 0xFFFFFFFF, 0, 1, Timing0, Timing1, 0)

        status = CANalystII.VCI_InitCAN(
            VCI_USBCAN2,
            device,
            channel,
            byref(self.init_config)
        )

        if status == STATUS_ERR:
            self.shutdown()
            raise ValueError("VCI_InitCAN Error, incorrect channel number?")

        status = CANalystII.VCI_StartCAN(
            VCI_USBCAN2,
            device,
            channel
        )

        if status == STATUS_ERR:
            logger.error("VCI_StartCAN Error, device:{0} channel:{1}".format(device, channel))
            self.shutdown()
            return

    def board_info(self) -> Dict:
        """
        Adapter Information

        :return: dictionary containing the following keys

            * `hardware_version`: `int`
            * `firmware_version`: `int`
            * `driver_version`: `int`
            * `library_version`: `int`
            * `irq`: `int`
            * `num_can_interfaces`: `int`
            * `serial_number`: `str`
            * `hardware_type`: `str`

        :rtype: dict
        """
        return {key: value for key, value in self._b_info.items()}

    def send(self, msg, timeout=None):
        """
        Send CAN Frame

        :param msg: message to send
        :type msg: :class:`can.Message`

        :param timeout: timeout is not used here
        :type timeout: None

        :return: `True` if frame was sent else `False`
        :rtype: bool
        """

        can_objs = (VCI_CAN_OBJ * 1)()

        can_objs[0].ID = msg.arbitration_id
        can_objs[0].ExternFlag = int(msg.is_extended_id)
        can_objs[0].SendType = 1
        can_objs[0].RemoteFlag = int(msg.is_remote_frame)
        can_objs[0].DataLen = msg.dlc
        for j in range(msg.dlc):
            can_objs[0].Data[j] = msg.data[j]

        frames_sent = CANalystII.VCI_Transmit(
            VCI_USBCAN2,
            self.device,
            self.channel,
            byref(can_objs),
            1
        )

        return bool(frames_sent)

    def available(self) -> int:
        """
        Check the number of frames waiting to be received.

        :return: number of available frames
        :rtype: int
        """

        return CANalystII.VCI_GetReceiveNum(VCI_USBCAN2, self.device, self.channel)

    def _recv_internal(self, timeout):
        raw_message = (VCI_CAN_OBJ * 1)()

        timeout = -1 if timeout is None else int(timeout * 1000)

        recv_count = CANalystII.VCI_Receive(
            VCI_USBCAN2, self.device, self.channel, byref(raw_message), 1, timeout
        )

        if not recv_count:
            return None, False

        message = Message(
            timestamp=raw_message[0].TimeStamp if raw_message[0].TimeFlag else 0.0,
            arbitration_id=raw_message[0].ID,
            is_remote_frame=bool(raw_message[0].RemoteFlag),
            is_extended_id=bool(raw_message[0].ExternFlag),
            channel=self.channel,
            dlc=raw_message[0].DataLen,
            data=[raw_message[0].Data[i] for i in range(raw_message[0].DataLen)],
        )

        return message, False

    def flush_tx_buffer(self):
        CANalystII.VCI_ClearBuffer(VCI_USBCAN2, self.device, self.channel)

    def shutdown(self):
        # stops receiving new frames
        try:
            CANalystII.VCI_ResetCAN(VCI_USBCAN2, self.device, self.channel)
        except:
            pass

        _in_use[self.device].remove(self)

        if len(_in_use[self.device]) == 0:
            CANalystII.VCI_CloseDevice(VCI_USBCAN2, self.device)
            del _in_use[self.device]

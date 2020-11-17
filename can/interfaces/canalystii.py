from ctypes import *
import logging
import platform
from can import BusABC, Message
from typing import List, Optional, Tuple, Union, Dict

logger = logging.getLogger(__name__)


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


# typedef  struct  _VCI_BOARD_INFO{
# 		USHORT	hw_Version;
# 		USHORT	fw_Version;
# 		USHORT	dr_Version;
# 		USHORT	in_Version;
# 		USHORT	irq_Num;
# 		BYTE	can_Num;
# 		CHAR	str_Serial_Num[20];
# 		CHAR	str_hw_Type[40];
# 		USHORT	Reserved[4];
# } VCI_BOARD_INFO,*PVCI_BOARD_INFO;
class _VCI_BOARD_INFO(Structure):
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


VCI_BOARD_INFO = _VCI_BOARD_INFO

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


class CANalystIIBus(BusABC):
    def __init__(
        self,
        channel: Union[int, List, Tuple, str],
        device: int = 0,
        bitrate: Optional[int, List, Tuple] = None,
        Timing0: Optional[int, List, Tuple] = None,
        Timing1: Optional[int, List, Tuple] = None,
        can_filters=None,
        **kwargs,
    ):
        """
        CANalystII Interface

        :param channel: The indexes of the channel(s) to initilize.
            If only a single channel is to be initilized you can pass an `int`,
            otherwise you will need to pass a list of channel numbers.
        :type channel: int, list, tuple

        :param device: device index. If there is more then one adapter the index number will be
            incremented by one for each additional adapter.
        :type device: int

        :param bitrate: CAN network bandwidth (bits/s).
            If you have more then a single channel supplied then you will want to pass a list of bitrates,
            one for each channel
        :type bitrate: int, list, tuple, None

        :param Timing0: customize the timing register if bitrate is not specified.
            If you have more then a single channel supplied then you will want to pass a list of Timing0 values,
            one for each channel
        :type Timing0: int, list, tuple, None

        :param Timing1: customize the timing register if bitrate is not specified.
            If you have more then a single channel supplied then you will want to pass a list of Timing1 values,
            one for each channel
        :type Timing1: int, list, tuple, None

        :param can_filters: filters for packet
        """

        if CANalystII is None:
            raise RuntimeError('CANalystII library failed to load.')

        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(",")]

        if bitrate is None:
            if isinstance(Timing0, int):
                Timing0 = [Timing0] * len(self.channels)
            if isinstance(Timing1, int):
                Timing1 = [Timing1] * len(self.channels)

        elif isinstance(bitrate, int):
            bitrate = [bitrate] * len(self.channels)

        self.device = device

        self.channel_info = "CANalyst-II: device {}, channels {}".format(
            self.device, self.channels
        )

        if bitrate is not None:
            Timing0 = []
            Timing1 = []

            for brate in bitrate:
                try:
                    t0, t1 = TIMING_DICT[brate]
                    Timing0 += [t0]
                    Timing1 += [t1]
                except KeyError:
                    raise ValueError("Bitrate is not supported ({0})".format(brate))

        if not Timing0 or not Timing1:
            raise ValueError("Timing registers are not set")

        try:
            CANalystII.VCI_UsbDeviceReset(VCI_USBCAN2, self.device, 0)
        except:
            pass

        self._b_info = VCI_BOARD_INFO()
        CANalystII.VCI_ReadBoardInfo(VCI_USBCAN2, device, byref(self._b_info))

        if CANalystII.VCI_OpenDevice(VCI_USBCAN2, self.device, 0) == STATUS_ERR:
            logger.error("VCI_OpenDevice Error")

        self.init_config = []

        for i, chan in enumerate(self.channels):
            t0 = Timing0[i]
            t1 = Timing1[i]
            init_config = VCI_INIT_CONFIG(0, 0xFFFFFFFF, 0, 1, t0, t1, 0)

            status = CANalystII.VCI_InitCAN(
                VCI_USBCAN2,
                self.device,
                chan,
                byref(init_config)
            )

            if status == STATUS_ERR:
                logger.error("VCI_InitCAN Error ({0})".format(chan))
                self.shutdown()
                return

            status = CANalystII.VCI_StartCAN(
                VCI_USBCAN2,
                self.device,
                chan
            )

            if status == STATUS_ERR:
                logger.error("VCI_StartCAN Error ({0})".format(chan))
                self.shutdown()
                return

            self.init_config += [init_config]

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
        return dict(
            hardware_version=self._b_info.hw_Version,
            firmware_version=self._b_info.fw_Version,
            driver_version=self._b_info.dr_Version,
            library_version=self._b_info.in_Version,
            irq=self._b_info.irq_Num,
            num_can_interfaces=self._b_info.can_Num,
            serial_number=str(self._b_info.str_Serial_Num, encoding='ascii'),
            hardware_type=str(self._b_info.str_hw_Type, encoding='ascii')
        )

    def send(self, msg, timeout=None):
        """
        Send CAN Frame(s)

        :param msg: message to send or a list of messages to be sent
        :type msg: :class:`can.Message`, list(:class:`can.Message`)

        :param timeout: timeout is not used here
        :return: list containing the number of frames sent for each channel
        :rtype: list(int)
        """
        if not isinstance(msg, (list, tuple)):
            msg = [msg]

        channels = {}
        for message in msg:
            if message.channel is not None:
                channel = message.channel
            elif len(self.channels) == 1:
                channel = self.channels[0]
            else:
                raise ValueError("msg.channel must be set when using multiple channels.")

            if channel not in channels:
                channels[channel] = 0

            channels[channel] += 1

        res = []

        for channel, count in channels.items():
            can_objs = (VCI_CAN_OBJ * count)()
            offset = 0

            for i, message in enumerate(msg):
                if message.channel is not None and message.channel != channel:
                    offset += 1
                    continue

                can_objs[i - offset].ID = message.arbitration_id
                can_objs[i - offset].ExternFlag = int(message.is_extended_id)
                can_objs[i - offset].SendType = 1
                can_objs[i - offset].RemoteFlag = int(message.is_remote_frame)
                can_objs[i - offset].DataLen = message.dlc
                for j in range(message.dlc):
                    can_objs[i - offset].Data[j] = message.data[j]

            frames_sent = CANalystII.VCI_Transmit(
                VCI_USBCAN2,
                self.device,
                channel,
                byref(can_objs),
                count
            )

            res += [frames_sent]

    def available(self, channel):
        """
        Check the number of frames waiting to be received.

        :param channel: channle number you want to check
        :type channel: int

        :return: number of available frames
        :rtype: int
        """
        return CANalystII.VCI_GetReceiveNum(VCI_USBCAN2, self.device, channel)

    def _recv_internal(self, timeout):
        return self.recv(timeout=timeout), False

    def recv(
        self,
        timeout: Optional[float] = None,
        channel: Optional[int] = None
    ) -> Optional[Message]:
        """
        Receive CAN Frames(s)

        :param timeout: fractional seconds or `None` to block until a packet has been received
        :type timeout: float, None

        :param channel: channel number to receive from.
            If only a single channel has been initilized this can be left at it's default of `None`.
        :type channel: int, None

        :returns: received message
        :rtype: :class:`can.Message`

        :raises: `ValueError` if supplied channel has not been initilized.
        """
        raw_message = (VCI_CAN_OBJ * 1)()

        timeout = -1 if timeout is None else int(timeout * 1000)

        if channel is None:
            channel = self.channels[0]

        if channel not in self.channels:
            raise ValueError("channel {0} has not been initilized".format(channel))

        if not self.available(channel):
            return

        CANalystII.VCI_Receive(
            VCI_USBCAN2, self.device, channel, byref(raw_message), 1, timeout
        )

        return Message(
                timestamp=raw_message[0].TimeStamp if raw_message[0].TimeFlag else 0.0,
                arbitration_id=raw_message[0].ID,
                is_remote_frame=bool(raw_message[0].RemoteFlag),
                is_extended_id=bool(raw_message[0].ExternFlag),
                channel=channel,
                dlc=raw_message[0].DataLen,
                data=raw_message[0].Data,
            )

    def flush_tx_buffer(self):
        for channel in self.channels:
            CANalystII.VCI_ClearBuffer(VCI_USBCAN2, self.device, channel)

    def shutdown(self):
        CANalystII.VCI_CloseDevice(VCI_USBCAN2, self.device)

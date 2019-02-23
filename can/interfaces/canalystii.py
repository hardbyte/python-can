from ctypes import *
import logging
import platform
from can import BusABC, Message

logger = logging.getLogger(__name__)


class VCI_INIT_CONFIG(Structure):
    _fields_ = [("AccCode", c_int32),
                ("AccMask", c_int32),
                ("Reserved", c_int32),
                ("Filter", c_ubyte),
                ("Timing0", c_ubyte),
                ("Timing1", c_ubyte),
                ("Mode", c_ubyte)]


class VCI_CAN_OBJ(Structure):
    _fields_ = [("ID", c_uint),
                ("TimeStamp", c_int),
                ("TimeFlag", c_byte),
                ("SendType", c_byte),
                ("RemoteFlag", c_byte),
                ("ExternFlag", c_byte),
                ("DataLen", c_byte),
                ("Data", c_ubyte * 8),
                ("Reserved", c_byte * 3)]


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
    def __init__(self, channel, device=0, baud=None, Timing0=None, Timing1=None, can_filters=None):
        """

        :param channel: channel number
        :param device: device number
        :param baud: baud rate
        :param Timing0: customize the timing register if baudrate is not specified
        :param Timing1:
        :param can_filters: filters for packet
        """
        super(CANalystIIBus, self).__init__(channel, can_filters)

        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(',')]

        self.device = device

        self.channel_info = "CANalyst-II: device {}, channels {}".format(self.device, self.channels)

        if baud is not None:
            try:
                Timing0, Timing1 = TIMING_DICT[baud]
            except KeyError:
                raise ValueError("Baudrate is not supported")

        if Timing0 is None or Timing1 is None:
            raise ValueError("Timing registers are not set")

        self.init_config = VCI_INIT_CONFIG(0, 0xFFFFFFFF, 0, 1, Timing0, Timing1, 0)

        if CANalystII.VCI_OpenDevice(VCI_USBCAN2, self.device, 0) == STATUS_ERR:
            logger.error("VCI_OpenDevice Error")

        for channel in self.channels:
            if CANalystII.VCI_InitCAN(VCI_USBCAN2, self.device, channel, byref(self.init_config)) == STATUS_ERR:
                logger.error("VCI_InitCAN Error")
                self.shutdown()
                return

            if CANalystII.VCI_StartCAN(VCI_USBCAN2, self.device, channel) == STATUS_ERR:
                logger.error("VCI_StartCAN Error")
                self.shutdown()
                return

    def send(self, msg, timeout=None):
        """

        :param msg: message to send
        :param timeout: timeout is not used here
        :return:
        """
        extern_flag = 1 if msg.is_extended_id else 0
        raw_message = VCI_CAN_OBJ(msg.arbitration_id, 0, 0, 1, msg.is_remote_frame, extern_flag, msg.dlc, (c_ubyte * 8)(*msg.data), (c_byte * 3)(*[0, 0, 0]))

        if msg.channel is not None:
            channel = msg.channel
        elif len(self.channels) == 1:
            channel = self.channels[0]
        else:
            raise ValueError(
                "msg.channel must be set when using multiple channels.")

        CANalystII.VCI_Transmit(VCI_USBCAN2, self.device, channel, byref(raw_message), 1)

    def _recv_internal(self, timeout=None):
        """

        :param timeout: float in seconds
        :return:
        """
        raw_message = VCI_CAN_OBJ()

        timeout = -1 if timeout is None else int(timeout * 1000)

        if CANalystII.VCI_Receive(VCI_USBCAN2, self.device, self.channels[0], byref(raw_message), 1, timeout) <= STATUS_ERR:
            return None, False
        else:
            return (
                Message(
                    timestamp=raw_message.TimeStamp if raw_message.TimeFlag else 0.0,
                    arbitration_id=raw_message.ID,
                    is_remote_frame=raw_message.RemoteFlag,
                    channel=0,
                    dlc=raw_message.DataLen,
                    data=raw_message.Data,
                ),
                False,
            )

    def flush_tx_buffer(self):
        for channel in self.channels:
            CANalystII.VCI_ClearBuffer(VCI_USBCAN2, self.device, channel)

    def shutdown(self):
        CANalystII.VCI_CloseDevice(VCI_USBCAN2, self.device)

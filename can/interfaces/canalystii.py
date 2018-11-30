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
    def __init__(self, channel, can_filters=None):
        super(CANalystIIBus, self).__init__(channel, can_filters)

        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(',')]

        self.init_config = VCI_INIT_CONFIG(0, 0xFFFFFFFF, 0, 1, 0x00, 0x1C, 0)

        if CANalystII.VCI_OpenDevice(VCI_USBCAN2, 0, 0) == STATUS_ERR:
            logger.error("VCI_OpenDevice Error")

        for channel in self.channels:
            if CANalystII.VCI_InitCAN(VCI_USBCAN2, 0, channel, byref(self.init_config)) == STATUS_ERR:
                logger.error("VCI_InitCAN Error")
                self.shutdown()
                return

            if CANalystII.VCI_StartCAN(VCI_USBCAN2, 0, channel) == STATUS_ERR:
                logger.error("VCI_StartCAN Error")
                self.shutdown()
                return

    def send(self, msg, timeout=None):
        """

        :param msg: message to send
        :param timeout: timeout is not used here
        :return:
        """
        raw_message = VCI_CAN_OBJ(msg.arbitration_id, 0, 0, 0, 0, 0, msg.dlc, (c_ubyte * 8)(*msg.data), (c_byte * 3)(*[0, 0, 0]))

        if msg.channel is not None:
            channel = msg.channel
        elif len(self.channels) == 1:
            channel = self.channels[0]
        else:
            raise ValueError(
                "msg.channel must be set when using multiple channels.")

        CANalystII.VCI_Transmit(VCI_USBCAN2, 0, channel, byref(raw_message), 1)

    def _recv_internal(self, timeout=None):
        """

        :param timeout: float in seconds
        :return:
        """
        raw_message = VCI_CAN_OBJ()

        timeout = -1 if timeout is None else int(timeout * 1000)

        if CANalystII.VCI_Receive(VCI_USBCAN2, 0, self.channels[0], byref(raw_message), 1, timeout) <= STATUS_ERR:
            return None, False
        else:
            return Message(arbitration_id=raw_message.ID, channel=0, data=raw_message.Data), False

    def shutdown(self):
        CANalystII.VCI_CloseDevice(VCI_USBCAN2, 0)

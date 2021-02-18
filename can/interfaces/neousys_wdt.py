#
# This kind of interface can be found for example on Neousys POC-551VTC
# One needs to have correct drivers and DLL (Share object for Linux) from Neousys
#
# https://www.neousys-tech.com/en/support-service/resources/category/299-poc-551vtc-driver
#
# Beware this is only tested on Linux kernel higher thant 5.3. This should be drop in
# with Windows but you have to replace with correct named DLL
#

import warnings
from ctypes import *
import threading
import logging
import platform
import time
from can import BusABC, Message

logger = logging.getLogger(__name__)


class WDT_CAN_SETUP(Structure):
    _fields_ = [
        ("bitRate", c_uint),
        ("recvConfig", c_uint),
        ("recvId", c_uint),
        ("recvMask", c_uint),
    ]


class WDT_CAN_MSG(Structure):
    _fields_ = [
        ("id", c_uint),
        ("flags", c_ushort),
        ("extra", c_ubyte),
        ("len", c_ubyte),
        ("data", c_ubyte * 8),
    ]


# valid:2~16, sum of the Synchronization, Propagation, and Phase Buffer 1 segments, measured in time quanta.
# valid:1~8, the Phase Buffer 2 segment in time quanta.
# valid:1~4, Resynchronization Jump Width in time quanta
# valid:1~1023, CAN_CLK divider used to determine time quanta
class WDT_CAN_BITCLK(Structure):
    _fields_ = [
        ("syncPropPhase1Seg", c_ushort),
        ("phase2Seg", c_ushort),
        ("jumpWidth", c_ushort),
        ("quantumPrescaler", c_ushort),
    ]


WDT_CAN_MSG_CALLBACK = CFUNCTYPE(None, POINTER(WDT_CAN_MSG), c_uint)
WDT_CAN_STATUS_CALLBACK = CFUNCTYPE(None, c_uint)

WDT_CAN_MSG_EXTENDED_ID = 0x0004
WDT_CAN_MSG_REMOTE_FRAME = 0x0040
WDT_CAN_MSG_DATA_NEW = 0x0080
WDT_CAN_MSG_DATA_LOST = 0x0100

WDT_CAN_MSG_USE_ID_FILTER = 0x00000008
WDT_CAN_MSG_USE_DIR_FILTER = (
    0x00000010 | WDT_CAN_MSG_USE_ID_FILTER
)  # only accept the direction specified in the message type
WDT_CAN_MSG_USE_EXT_FILTER = (
    0x00000020 | WDT_CAN_MSG_USE_ID_FILTER
)  # filters on only extended identifiers

WDT_CAN_STATUS_BUS_OFF = 0x00000080
WDT_CAN_STATUS_EWARN = (
    0x00000040  # can controller error level has reached warning level.
)
WDT_CAN_STATUS_EPASS = (
    0x00000020  # can controller error level has reached error passive level.
)
WDT_CAN_STATUS_LEC_STUFF = 0x00000001  # a bit stuffing error has occurred.
WDT_CAN_STATUS_LEC_FORM = 0x00000002  # a formatting error has occurred.
WDT_CAN_STATUS_LEC_ACK = 0x00000003  # an acknowledge error has occurred.
WDT_CAN_STATUS_LEC_BIT1 = (
    0x00000004  # the bus remained a bit level of 1 for longer than is allowed.
)
WDT_CAN_STATUS_LEC_BIT0 = (
    0x00000005  # the bus remained a bit level of 0 for longer than is allowed.
)
WDT_CAN_STATUS_LEC_CRC = 0x00000006  # a crc error has occurred.
WDT_CAN_STATUS_LEC_MASK = (
    0x00000007  # this is the mask for the can last error code (lec).
)


class NeousysWdtBus(BusABC):
    def __init__(self, channel, device=0, bitrate=500000, **kwargs):
        """
        :param channel: channel number
        :param device: device number
        :param bitrate: bit rate. Renamed to bitrate in next release.
        """
        super(NeousysWdtBus, self).__init__(channel, **kwargs)

        self.canlib = None

        try:
            if platform.system() == "Windows":
                self.canlib = WinDLL("./WDT_DIO.dll")
            else:
                self.canlib = CDLL("libwdt_dio.so")

            logger.info("Loaded Neousys WDT_DIO Can driver")

            self.channel = channel

            self.device = device

            self.channel_info = "Neousys WDT_DIO Can: device {}, channel {}".format(
                self.device, self.channel
            )

            self.lock = threading.Lock()
            self.recv_msg_array = []

            # Init with accept all and wanted bitrate
            self.init_config = WDT_CAN_SETUP(bitrate, WDT_CAN_MSG_USE_ID_FILTER, 0, 0)

            # These can be needed in some old 2.x consepts not needed in 3.6 though
            # self.canlib.CAN_RegisterReceived.argtypes = [c_uint, WDT_CAN_MSG_CALLBACK]
            # self.canlib.CAN_RegisterReceived.restype = c_int
            # self.canlib.CAN_RegisterStatus.argtypes = [c_uint, WDT_CAN_STATUS_CALLBACK]
            # self.canlib.CAN_RegisterStatus.restype = c_int

            self._WDTCAN_Received = WDT_CAN_MSG_CALLBACK(self._WDTCAN_Received)
            self._WDTCAN_Status = WDT_CAN_STATUS_CALLBACK(self._WDTCAN_Status)

            if self.canlib.CAN_RegisterReceived(0, self._WDTCAN_Received) == 0:
                logger.error("Neousys WDT_DIO CANBus Setup receive callback")

            if self.canlib.CAN_RegisterStatus(0, self._WDTCAN_Status) == 0:
                logger.error("Neousys WDT_DIO CANBus Setup status callback")

            if (
                self.canlib.CAN_Setup(
                    channel, byref(self.init_config), sizeof(self.init_config)
                )
                == 0
            ):
                logger.error("Neousys WDT_DIO CANBus Setup Error")

            if self.canlib.CAN_Start(channel) == 0:
                logger.error("Neousys WDT_DIO CANBus Start Error")

        except OSError as e:
            logger.info("Cannot Neousys WDT_DIO CANBus dll or share object")

    def send(self, msg, timeout=None):
        """
        :param msg: message to send
        :param timeout: timeout is not used here
        :return:
        """

        if self.canlib is None:
            logger.error("Can't send msg as Neousys WDT_DIO DLL/SO is not loaded")
        else:
            tx_msg = WDT_CAN_MSG(
                msg.arbitration_id, 0, 0, msg.dlc, (c_ubyte * 8)(*msg.data)
            )

            if self.canlib.CAN_Send(self.channel, byref(tx_msg), sizeof(tx_msg)) == 0:
                logger.error("Neousys WDT_DIO Can can't send message")

    def _recv_internal(self, timeout):
        msg = None

        # If there is message waiting in array
        # pass it as new message
        if len(self.recv_msg_array) > 0:
            self.lock.acquire()
            msg = self.recv_msg_array.pop(0)
            self.lock.release()

        return msg, False

    def _WDTCAN_Received(self, lpMsg, cbMsg):
        """
        :param lpMsg struct CAN_MSG
        :param cbMsg message number
        :return:
        """
        remote_frame = False
        extended_frame = False

        msg_bytes = bytearray(lpMsg.contents.data)

        if lpMsg.contents.flags & WDT_CAN_MSG_REMOTE_FRAME:
            remote_frame = True

        if lpMsg.contents.flags & WDT_CAN_MSG_EXTENDED_ID:
            extended_frame = True

        if lpMsg.contents.flags & WDT_CAN_MSG_DATA_LOST:
            logger.error("_WDTCAN_Received flag CAN_MSG_DATA_LOST")

        msg = Message(
            timestamp=time.time(),
            arbitration_id=lpMsg.contents.id,
            is_remote_frame=remote_frame,
            is_extended_id=extended_frame,
            channel=self.channel,
            dlc=lpMsg.contents.len,
            data=msg_bytes[: lpMsg.contents.len],
        )

        # Reading happens in Callback function and
        # with Python-CAN it happens polling
        # so cache stuff in array to for poll
        self.lock.acquire()
        self.recv_msg_array.append(msg)
        self.lock.release()

    def _WDTCAN_Status(status):
        """
        :param status BUS Status
        :return:
        """

        logger.info("_WDTCAN_Status" + str(status))

    def shutdown(self):
        if self.canlib is not None:
            logger.error(
                "No need Can't send msg as Neousys WDT_DIO DLL/SO is not loaded"
            )
        else:
            self.canlib.CAN_Stop(self.channel)

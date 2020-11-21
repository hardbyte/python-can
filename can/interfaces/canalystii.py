from ctypes import *
import logging
import platform
from can import BusABC, Message
from typing import Optional, Dict, Union
from ..typechecking import CanFilters

logger = logging.getLogger(__name__)

VCI_USBCAN2 = 4
STATUS_OK = 0x01
STATUS_ERR = 0x00

ERR_CAN_OVERFLOW = 0x0001
ERR_CAN_ERRALARM = 0x0002
ERR_CAN_PASSIVE = 0x0004
ERR_CAN_LOSE = 0x0008
ERR_CAN_BUSERR = 0x0010

ERR_DEVICEOPENED = 0x0100
ERR_DEVICEOPEN = 0x0200
ERR_DEVICENOTOPEN = 0x0400
ERR_BUFFEROVERFLOW = 0x0800
ERR_DEVICENOTEXIST = 0x1000
ERR_LOADKERNELDLL = 0x2000
ERR_CMDFAILED = 0x4000
ERR_BUFFERCREATE = 0x8000

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


class CANalystIIException(Exception):
    errno = None
    msg = ''

    def __init__(self, msg=None, errno=None):
        if msg is not None:
            self.msg = msg
        if errno is not None:
            self.errno = errno

    def __str__(self):
        return self.msg + ' ' + '({0})'.format(self.errno)


class CANalystIIStartupError(CANalystIIException):
    pass


class CanalystIIBitrateDetectFailed(CANalystIIException):
    msg = 'Failed to detect bitrate.'
    errno = 1000


class CanalystIIChannelInUse(CANalystIIException):
    msg = 'Channel {0} already in use for device {1}'
    errno = 1001

    def __init__(self, device, channel):
        self.msg = self.msg.format(device, channel)
        CANalystIIException.__init__(self)


class CanalystIIInvalidTimings(CANalystIIException):
    msg = 'Timing registers are not set.'
    errno = 1002


class CanalystIIBitrateNotSupported(CANalystIIException):
    msg = 'Bitrate is not supported.'


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


class VCI_CAN_STATUS(Structure):
    _fields_ = [
        ('ErrInterrupt', c_ubyte),
        ('regMode', c_ubyte),
        ('regStatus', c_ubyte),
        ('regALCapture', c_ubyte),
        ('regECCapture', c_ubyte),
        ('regEWLimit', c_ubyte),
        ('regRECounter', c_ubyte),
        ('regTECounter', c_ubyte),
        ('Reserved', c_ulong)
    ]


class VCI_ERR_INFO(Structure):
    _fields_ = [
        ('ErrCode;', c_uint),
        ('Passive_ErrData', c_byte * 3),
        ('ArLost_ErrData', c_byte)
    ]


_in_use = {}


class CANalystIIBus(BusABC):
    CANalystIIException = CANalystIIException
    CANalystIIStartupError = CANalystIIStartupError
    CanalystIIBitrateDetectFailed = CanalystIIBitrateDetectFailed
    CanalystIIChannelInUse = CanalystIIChannelInUse
    CanalystIIInvalidTimings = CanalystIIInvalidTimings
    CanalystIIBitrateNotSupported = CanalystIIBitrateNotSupported

    def __init__(
        self,
        channel: Union[int, str],
        device: int = 0,
        bitrate: Optional[int] = None,
        Timing0: Optional[int] = None,
        Timing1: Optional[int] = None,
        can_filters: CanFilters = None,
        **kwargs,
    ):
        """
        CANalystII Interface

        :param channel: channel number to use
        :type channel: int, str

        :param device: device index. If there is more then one adapter the index number
            will be incremented by one for each additional adapter.
        :type device: int

        :param bitrate: CAN network bandwidth (bits/s).
        :type bitrate: int, optional

        :param Timing0: customize the timing register if bitrate is not specified.
        :type Timing0: int, optional

        :param Timing1: customize the timing register if bitrate is not specified.
        :type Timing1: int, optional

        :param can_filters: filters for packet
        :type can_filters: CanFilters

        :raises: RuntimeError, ValueError, CANalystIIStartupError, CanalystIIChannelInUse,
            CanalystIIBitrateDetectFailed, CanalystIIBitrateNotSupported
        """

        if CANalystII is None:
            raise RuntimeError('CANalystII library failed to load.')

        if (
            isinstance(channel, (list, tuple)) or
            (isinstance(channel, str) and not channel.isdigit())
        ):
            raise ValueError(
                'This class no longer supports multiple channels, '
                'create an instance for each channel'
            )

        channel = int(channel)

        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

        self.channel = channel
        self.device = device
        self.channel_info = "CANalyst-II: device {}, channel {}".format(
            device,
            channel
        )

        if device not in _in_use:
            # this has exception catching because not all of the variations
            # of the ControlCAN library have this function available.
            # The ones that do have it available seem to have less issues
            # when resetting the device before opening it.
            try:
                CANalystII.VCI_UsbDeviceReset(VCI_USBCAN2, device, 0)
            except:
                pass

            b_info = VCI_BOARD_INFO()
            status = CANalystII.VCI_ReadBoardInfo(
                VCI_USBCAN2,
                device,
                byref(b_info)
            )

            if status != STATUS_OK:
                logger.error("VCI_ReadBoardInfo Error ({0})".format(status))

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

            status = CANalystII.VCI_OpenDevice(VCI_USBCAN2, self.device, 0)

            if status != STATUS_OK:
                raise CANalystIIStartupError(
                    'Unable to open interface, the device number '
                    'supplied may be incorrect',
                    status
                )

            _in_use[device] = []
        else:
            for cb in _in_use[device]:
                if cb.channel == channel:
                    raise CanalystIIChannelInUse(channel,  device)

            self._b_info = _in_use[device][0].board_info

        _in_use[device] += [self]

        init_config = VCI_INIT_CONFIG()
        init_config.AccMask = 0xFFFFFFFF
        init_config.Filter = 1

        # autodetect bitrate
        if bitrate is None and Timing0 is None and Timing1 is None:
            logger.info('autodetecting bitrate')
            for bitrate, (Timing0, Timing1) in TIMING_DICT.items():
                logger.info('bitrate autodetect: {0}'.format(bitrate))
                init_config.Timing0 = Timing0
                init_config.Timing1 = Timing1

                status = CANalystII.VCI_InitCAN(
                    VCI_USBCAN2,
                    device,
                    channel,
                    byref(init_config)
                )

                if status != STATUS_OK:
                    continue

                status = CANalystII.VCI_StartCAN(
                    VCI_USBCAN2,
                    device,
                    channel
                )

                if status != STATUS_OK:
                    continue

                msg = self.recv(timeout=0.5)

                CANalystII.VCI_ResetCAN(
                    VCI_USBCAN2,
                    device,
                    channel
                )

                if msg is not None:
                    logger.info('bitrate detected: {0}'.format(bitrate))
                    break
            else:
                self.shutdown()
                raise CanalystIIBitrateDetectFailed()

        elif bitrate is not None:
            if bitrate in TIMING_DICT:
                Timing0, Timing1 = TIMING_DICT[bitrate]
            else:
                self.shutdown()
                raise CanalystIIBitrateNotSupported(errno=bitrate)

        elif None in (Timing0, Timing1):
            self.shutdown()
            raise CanalystIIInvalidTimings()

        init_config.Timing0 = Timing0
        init_config.Timing1 = Timing1

        self.init_config = init_config

        status = CANalystII.VCI_InitCAN(
            VCI_USBCAN2,
            device,
            channel,
            byref(self.init_config)
        )

        if status != STATUS_OK:
            self.shutdown()
            raise CANalystIIStartupError(
                "VCI_InitCAN Error, incorrect channel number?",
                status
            )

        status = CANalystII.VCI_StartCAN(
            VCI_USBCAN2,
            device,
            channel
        )

        if status != STATUS_OK:
            logger.error(
                "VCI_StartCAN Error ({0}), device:{1} "
                "channel:{2}".format(status, device, channel)
            )
            logger.info('receiving failed to start, only able to transmit.')

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

    def send(self, msg: Message, timeout=None):
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

        arbitration_id = msg.arbitration_id
        if arbitration_id & 0x80000000:
            extended = 1
            arbitration_id &= 0x7FFFFFFF
        else:
            extended = int(msg.is_extended_id)

        can_objs[0].ID = arbitration_id
        can_objs[0].ExternFlag = extended
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

    def status(self) -> Dict:
        """
        CAN Status

        returns a dictionary with the following keys

            * `err_interrupt`
            * `mode`
            * `status`
            * `al_capture`
            * `ec_capture`
            * `ew_limit`
            * `rx_count`
            * `tx_count`

        :rtype: dict
        """
        status = VCI_CAN_STATUS()
        try:
            CANalystII.VCI_ReadCANStatus(
                VCI_USBCAN2,
                self.device,
                self.channel,
                byref(status)
            )

        except:
            pass

        return dict(
            err_interrupt=status.ErrInterrupt,
            mode=status.regMode,
            status=status.regStatus,
            al_capture=status.regALCapture,
            ec_capture=status.regECCapture,
            ew_limit=status.regEWLimit,
            rx_count=status.regRECounter,
            tx_count=status.regTECounter
        )

    def error_info(self) -> Dict:
        """
        CAN Error

        returns a dictionary with the following keys

        `error_code`
        `passive_err_data`
        `ar_lost_err_data`

        :rtype: dict
        """
        error_info = VCI_ERR_INFO()
        try:
            CANalystII.VCI_ReadErrInfo(
                VCI_USBCAN2,
                self.device,
                self.channel,
                byref(error_info)
            )
        except:
            pass

        return dict(
            error_code=error_info.ErrCode,
            passive_err_data=error_info.Passive_ErrData,
            ar_lost_err_data=error_info.ArLost_ErrData
        )

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
            data=bytearray([raw_message[0].Data[i] for i in range(raw_message[0].DataLen)]),
        )

        return message, False

    def flush_tx_buffer(self):
        CANalystII.VCI_ClearBuffer(VCI_USBCAN2, self.device, self.channel)

    def shutdown(self):
        # stops receiving new frames
        CANalystII.VCI_ResetCAN(VCI_USBCAN2, self.device, self.channel)

        _in_use[self.device].remove(self)

        if len(_in_use[self.device]) == 0:
            CANalystII.VCI_CloseDevice(VCI_USBCAN2, self.device)
            del _in_use[self.device]

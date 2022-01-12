import time
import ctypes

from can import BitTiming, BusABC, BusState, Message
from can import CanInitializationError, CanOperationError

from .vci import *
from .timing import ZlgBitTiming


DeviceType = ZCAN_DEVICE.USBCANFD_200U


class ZlgCanBus(BusABC):
    def __init__(self, channel, device=0, tres=True, **kwargs):
        """
        :param channel: channel index, [0, 1,,,]
        :param device: device index, [0, 1,,,]
        :param tres: enable/disable termination resistor on specified channel
        """
        bitrate = int(kwargs.get('bitrate', 500000))
        data_bitrate = int(kwargs.get('data_bitrate', bitrate))
        self.channel_info = \
            f'{self.__class__.__name__}{device}:{channel}@{bitrate}'
        if bitrate != data_bitrate:
            self.channel_info += f'/{data_bitrate}'
        self._dev_type = ZCAN_DEVICE_TYPE(DeviceType.value)
        self._dev_index = ZCAN_DEVICE_INDEX(int(device))
        self._dev_channel = ZCAN_CHANNEL(int(channel))
        self._opened = self.open(bitrate, data_bitrate)
        if not self._opened:
            raise CanInitializationError(f'Failed to open {self.channel_info}')
        self.tres = bool(tres)
        super().__init__(int(channel), **kwargs)

    @property
    def tres(self):
        '''Termination resistor'''
        return self._tres
    
    @tres.setter
    def tres(self, value):
        self._tres = bool(value)
        if not vci_channel_enable_tres(
            self._dev_type, self._dev_index, self._dev_channel, self._tres
        ):
            raise CanOperationError(
                f'Failed to {"enable" if value else "disable"} '
                f'termination resistor for {self.channel_info} !'
            )
    
    @property
    def state(self):
        err_msg = ZCAN_ERR_MSG()
        if not vci_channel_read_info(
            self._dev_type, self._dev_index, self._dev_channel, err_msg
        ):
            raise CanOperationError(
                f'Failed to read CAN{self._dev_channel} status!'
            )
        if err_msg.info.err:
            if err_msg.info.est:
                return BusState.ERROR
            else:
                return BusState.ACTIVE
        return None # https://github.com/hardbyte/python-can/issues/736
    
    @state.setter
    def state(self, value):
        raise NotImplementedError()

    def _from_raw(self, raw):
        return Message(
            timestamp       = raw.header.ts,
            arbitration_id  = raw.header.id,
            is_fd           = bool(raw.header.info.fmt),
            is_extended_id  = bool(raw.header.info.sef),
            is_remote_frame = bool(raw.header.info.sdf),
            is_error_frame  = bool(raw.header.info.err),
            bitrate_switch  = bool(raw.header.info.brs),
            dlc             = raw.header.len,
            data            = bytes(raw.dat[:raw.header.len]),
            channel         = raw.header.chn,
        )
    
    def _to_raw(self, msg):
        info = ZCAN_MSG_INFO(
            txm = False,
            fmt = msg.is_fd,
            sdf = msg.is_remote_frame,
            sef = msg.is_extended_id,
            err = msg.is_error_frame,
            brs = msg.bitrate_switch,
            est = msg.error_state_indicator,
            # pad
        )
        header = ZCAN_MSG_HDR(
            ts      = c_uint32(int(time.time())),
            id      = msg.arbitration_id,
            info    = info,
            chn     = self._dev_channel.value,
            len     = msg.dlc
        )
        if msg.is_fd:
            raw = ZCAN_FD_MSG(header=header)
        else:
            raw = ZCAN_20_MSG(header=header)
        ctypes.memmove(raw.dat, bytes(msg.data), msg.dlc)
        return raw
    
    def _recv_internal(self, timeout):
        timeout = c_uint32(int((timeout or 0)*1000))
        if vci_can_get_recv_num(
            self._dev_type, self._dev_index, self._dev_channel
        ) > 0:
            rx_buf = (ZCAN_20_MSG * 1)()
            if vci_can_recv(
                self._dev_type, self._dev_index, self._dev_channel,
                rx_buf, len(rx_buf), timeout
            ) > 0:
                return self._from_raw(rx_buf[0]), self.filters is None
            else:
                raise CanOperationError('Failed to receive message!')
        if vci_canfd_get_recv_num(
            self._dev_type, self._dev_index, self._dev_channel
        ) > 0:
            rx_buf = (ZCAN_FD_MSG * 1)()
            if vci_canfd_recv(
                self._dev_type, self._dev_index, self._dev_channel,
                rx_buf, len(rx_buf), timeout
            ) > 0:
                return self._from_raw(rx_buf[0]), self.filters is None
            else:
                raise CanOperationError('Failed to receive CANFD message!')
        time.sleep(.0001)    # Avoid high CPU usage if no message received
        return None, self.filters is None

    def send(self, msg, timeout=None) -> None:
        timeout = c_uint32(int((timeout or 0)*1000))
        if msg.is_fd:
            tx_buf = (ZCAN_FD_MSG * 1)()
            tx_buf[0] = self._to_raw(msg)
            if not vci_canfd_send(
                self._dev_type, self._dev_index, self._dev_channel,
                tx_buf, len(tx_buf)
            ):
                raise CanOperationError(
                    f'Failed to send CANFD message {msg.arbitration_id:03X}!'
                )
        else:
            tx_buf = (ZCAN_20_MSG * 1)()
            tx_buf[0] = self._to_raw(msg)
            if not vci_can_send(
                self._dev_type, self._dev_index, self._dev_channel,
                tx_buf, len(tx_buf)
            ):
                raise CanOperationError(
                    f'Failed to send CAN message {msg.arbitration_id:03X}!'
                )

    def open(self, bitrate, data_bitrate):
        timing = ZlgBitTiming(self._dev_type.value)
        if not vci_device_open(self._dev_type, self._dev_index):
            return False
        if not vci_channel_open(
            self._dev_type, self._dev_index, self._dev_channel,
            timing.f_clock,
            timing.timing(bitrate),
            timing.timing(data_bitrate)
        ):
            vci_device_close(self._dev_type, self._dev_index)
            return False
        else:
            return True

    def shutdown(self) -> None:
        super().shutdown()
        vci_channel_close(self._dev_type, self._dev_index, self._dev_channel)
        vci_device_close(self._dev_type, self._dev_index)

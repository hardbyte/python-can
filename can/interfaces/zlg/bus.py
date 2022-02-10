import time
import ctypes
import platform

from can import BusABC, BusState, Message
from can import CanInitializationError, CanOperationError, CanTimeoutError

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
        if platform.system() != "Linux":
            raise CanInitializationError(f'Only Linux is supported currently')
        self.bitrate = kwargs.get('bitrate', 500000)
        self.data_bitrate = kwargs.get('data_bitrate', None)
        self.channel_info = \
            f'{self.__class__.__name__}{device}:{channel}@{self.bitrate}'
        if self.data_bitrate:
            self.channel_info += f'/{self.data_bitrate}'
        self._dev_type = DeviceType.value
        self._dev_index = int(device)
        self._dev_channel = int(channel)
        self._dev_timestamp = time.time()
        self.is_opened = self.open()
        if not self.is_opened:
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
            ts      = (int(time.time() - self._dev_timestamp) * 1000) & 0xFFFF_FFFF,
            id      = msg.arbitration_id,
            info    = info,
            chn     = self._dev_channel,
            len     = msg.dlc
        )
        if msg.is_fd:
            raw = ZCAN_FD_MSG(header=header)
        else:
            raw = ZCAN_20_MSG(header=header)
        ctypes.memmove(raw.dat, bytes(msg.data), msg.dlc)
        return raw
    
    def _available_msgs(self) -> tuple[bool, int]:
        '''Return (is_fd, buffered_msg_count)'''
        can_msg_count = vci_can_get_recv_num(
            self._dev_type, self._dev_index, self._dev_channel
        )
        canfd_msg_count = vci_canfd_get_recv_num(
            self._dev_type, self._dev_index, self._dev_channel
        )
        if can_msg_count > 0 and canfd_msg_count > 0:
            if canfd_msg_count > can_msg_count:
                return True, canfd_msg_count
            else:
                return False, can_msg_count
        elif can_msg_count == 0 and canfd_msg_count == 0:
            return bool(self.data_bitrate), 0
        else:
            return canfd_msg_count > 0, canfd_msg_count or can_msg_count

    def _recv_one(self, fd) -> Message:
        delay = 1  # ZLG cann't comfirm what's happen if delay == 0
        rx_buf = (ZCAN_FD_MSG * 1)() if fd else (ZCAN_20_MSG * 1)()
        if fd:
            ret = vci_canfd_recv(
                self._dev_type, self._dev_index, self._dev_channel,
                rx_buf, len(rx_buf), delay
            )
        else:
            ret = vci_can_recv(
                self._dev_type, self._dev_index, self._dev_channel,
                rx_buf, len(rx_buf), delay
            )
        if ret > 0:
            return self._from_raw(rx_buf[0])
        else:
            return None

    def _recv_internal(self, timeout):
        t1 = time.time()
        while True:
            is_fd, msg_count = self._available_msgs()
            if msg_count:
                if msg := self._recv_one(is_fd):
                    return msg, self.filters is None
                else:
                    raise CanOperationError(f'Failed to receive!')
            elif timeout is None:
                time.sleep(0.001)
            elif timeout < 0.001:
                return None, self.filters is None
            elif (time.time() - t1) < timeout:
                time.sleep(0.001)
            else:
                raise CanTimeoutError(f'Receive timeout!')
    
    def _send_one(self, msg) -> int:
        tx_buf = (ZCAN_FD_MSG * 1)() if msg.is_fd else (ZCAN_20_MSG * 1)()
        tx_buf[0] = self._to_raw(msg)
        if msg.is_fd:
            return vci_canfd_send(
                self._dev_type, self._dev_index, self._dev_channel,
                tx_buf, len(tx_buf)
            )
        else:
            return vci_can_send(
                self._dev_type, self._dev_index, self._dev_channel,
                tx_buf, len(tx_buf)
            )
    
    def _send_internal(self, msg, timeout=None) -> None:
        while timeout is None:
            if self._send_one(msg):
                return
        else:
            t1 = time.time()
            while (time.time() - t1) < timeout or timeout < 0.001:
                if self._send_one(msg):
                    return
                elif timeout < 0.001:
                    return
            else:
                raise CanTimeoutError(
                    f'Send message {msg.arbitration_id:03X} timeout!'
                )
    
    def send(self, msg, timeout=None) -> None:
        # The maximum tx timeout is 4000ms, limited by firmware, as explained officially
        dev_timeout = 4000 if timeout is None else 10
        vci_channel_set_tx_timeout(
            self._dev_type, self._dev_index, self._dev_channel,
            dev_timeout
        )
        if self.data_bitrate: # Force FD if data_bitrate
            msg.is_fd = True
        self._send_internal(msg, timeout)

    def open(self) -> bool:
        timing = ZlgBitTiming(self._dev_type)
        clock = timing.f_clock
        bitrate = timing.timing(self.bitrate)
        if self.data_bitrate:
            data_bitrate = timing.timing(self.data_bitrate)
        else:
            data_bitrate = bitrate
        if not vci_device_open(self._dev_type, self._dev_index):
            return False
        if not vci_channel_open(
            self._dev_type, self._dev_index, self._dev_channel,
            clock, bitrate, data_bitrate
        ):
            vci_device_close(self._dev_type, self._dev_index)
            return False
        else:
            return True

    def shutdown(self) -> None:
        super().shutdown()
        vci_channel_close(self._dev_type, self._dev_index, self._dev_channel)
        vci_device_close(self._dev_type, self._dev_index)

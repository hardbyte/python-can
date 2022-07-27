import collections
import warnings
from typing import List, Optional, Tuple, Any, Union

import can
import can.typechecking
import ctypes
from can import CanInitializationError
from can.bus import LOG

from tosun import TSCanMessage, TSCanFdMessage, TSMasterException, TosunDevice, TSMasterMessageType


def tosun_convert_msg(msg):
    if isinstance(msg, TSCanMessage):
        return can.Message(
            timestamp=msg.FTimeUs,
            arbitration_id=msg.FIdentifier,
            is_extended_id=msg.FProperties & 0x04,
            is_remote_frame=msg.FProperties & 0x02,
            channel=msg.FIdxChn,
            dlc=msg.FDLC,
            data=bytes(msg.FData),
            is_fd=False,
            is_rx=False if msg.FProperties & 0x01 else True,
        )
    elif isinstance(msg, TSCanFdMessage):
        return can.Message(
            timestamp=msg.FTimeUs,
            arbitration_id=msg.FIdentifier,
            is_extended_id=msg.FProperties & 0x04,
            is_remote_frame=msg.FProperties & 0x02,
            channel=msg.FIdxChn,
            dlc=msg.FDLC,
            data=bytes(msg.FData),
            is_fd=False,
            is_rx=False if msg.FProperties & 0x01 else True,
            bitrate_switch=msg.FFDProperties & 0x02,
            error_state_indicator=msg.FFDProperties & 0x04,
        )
    elif isinstance(msg, can.Message):
        if msg.is_fd:
            result = TSCanFdMessage()
            result.FFDProperties = 0x00 | (0x02 if msg.bitrate_switch else 0x00) | \
                                   (0x04 if msg.error_state_indicator else 0x00)
        else:
            result = TSCanMessage()
        result.FIdxChn = msg.channel
        result.FProperties = 0x00 | (0x00 if msg.is_rx else 0x01) | \
                             (0x02 if msg.is_remote_frame else 0x00) | \
                             (0x04 if msg.is_extended_id else 0x00)
        result.FDLC = msg.dlc
        result.FIdentifier = msg.arbitration_id
        result.FTimeUs = int(msg.timestamp)
        for index, item in enumerate(msg.data):
            result.FData[index] = item
        return result
    else:
        raise TSMasterException(f'Unknown message type: {type(msg)}')


class TosunBus(can.BusABC):

    def __init__(self, mappings: list[dict],
                 configs: Union[List[dict], Tuple[dict]],
                 fifo_status: str = 'enable',
                 turbo_enable: bool = False,
                 receive_own_messages=True,
                 channel: Any = None,
                 rx_queue_size: Optional[int] = None,
                 can_filters: Optional[can.typechecking.CanFilters] = None,
                 **kwargs: object):
        super().__init__(channel, can_filters, **kwargs)
        self.receive_own_messages = receive_own_messages

        if isinstance(channel, list):
            self.channels = channel
        else:
            self.channels = []
        if 'with_com' not in kwargs:
            kwargs['with_com'] = False
        self.device = TosunDevice(self.channels, **kwargs)
        count = self.device.channel_count('can', len(mappings))
        assert count == len(mappings)
        self.available = []
        for _mapping in mappings:
            _mapping = self.device.mapping_instance(**_mapping)
            self.device.set_mapping(_mapping)
            if _mapping.FMappingDisabled is False:
                chl_index = _mapping.FAppChannelIndex
                if isinstance(chl_index, ctypes.c_int):
                    self.available.append(chl_index.value)
                else:
                    self.available.append(chl_index)

        for index, chl in enumerate(self.available):
            try:
                config: dict = configs[index]
            except IndexError:
                LOG.warn(f'TOSUN-CAN: channel:{chl} not initialized.')
                return

            baudrate = config.get('baudrate', None)
            if baudrate is None:
                raise CanInitializationError('TOSUN-CAN: baudrate is required.')

            del config['baudrate']
            baudrate = int(baudrate / 1000)
            config['kbaudrate'] = baudrate

            arb_baudrate = config.get('arb_baudrate', None)
            if arb_baudrate is None:
                arb_kbaudrate = baudrate
            else:
                del config['arb_baudrate']
                arb_kbaudrate = int(arb_baudrate / 1000)
            config['arb_kbaudrate'] = arb_kbaudrate

            self.device.configure_baudrate(chl, **config)

        self.device.turbo_mode(turbo_enable)
        try:
            self.device.set_receive_fifo_status(fifo_status)
        except TSMasterException as e:
            LOG.warning(e)
        # self.device.connect()
        self.rx_queue = collections.deque(
            maxlen=rx_queue_size
        )  # type: Deque[Any]               # channel, raw_msg

    def _recv_from_queue(self) -> Tuple[can.Message, bool]:
        """Return a message from the internal receive queue"""
        raw_msg = self.rx_queue.popleft()
        if isinstance(raw_msg, can.Message):
            return raw_msg, False
        return tosun_convert_msg(raw_msg), False

    def poll_received_messages(self, timeout):
        for channel in self.available:
            can_num = self.device.fifo_read_buffer_count(channel, TSMasterMessageType.CAN)
            canfd_num = self.device.fifo_read_buffer_count(channel, TSMasterMessageType.CAN_FD)
            if self.device.com_enabled:
                if can_num:
                    success, chl_index, is_remote, is_extend, dlc, can_id, timestamp, data = \
                        self.device.fifo_receive_msg(channel, self.receive_own_messages, TSMasterMessageType.CAN)
                    if success:
                        self.rx_queue.append(
                            can.Message(
                                timestamp=timestamp,
                                arbitration_id=can_id,
                                is_extended_id=is_extend,
                                is_remote_frame=is_remote,
                                channel=chl_index,
                                dlc=dlc,
                                data=[int(i) for i in data.split(',')],
                                is_fd=False,
                            )
                        )
                if canfd_num:
                    success, chl_index, is_remote, is_extend, is_edl, is_brs, dlc, can_id, timestamp, data = \
                        self.device.fifo_receive_msg(channel, self.receive_own_messages, TSMasterMessageType.CAN_FD)
                    if success:
                        self.rx_queue.append(
                            can.Message(
                                timestamp=timestamp,
                                arbitration_id=can_id,
                                is_extended_id=is_extend,
                                is_remote_frame=is_remote,
                                channel=chl_index,
                                dlc=dlc,
                                data=[int(i) for i in data.split(',')],
                                is_fd=True,
                                bitrate_switch=is_brs,

                            )
                        )
            if can_num:
                can_msg, can_num = self.device.tsfifo_receive_msgs(channel, can_num, self.receive_own_messages,
                                                                   TSMasterMessageType.CAN)
                LOG.debug(f'TOSUN-CAN: can message received: {can_num}.')
                self.rx_queue.extend(
                    can_msg[i] for i in range(can_num)
                )
            if canfd_num:
                can_msgfd, canfd_num = self.device.tsfifo_receive_msgs(channel, canfd_num, self.receive_own_messages,
                                                                       TSMasterMessageType.CAN_FD)
                LOG.debug(f'ZLG-CAN: canfd message received: {canfd_num}.')
                self.rx_queue.extend(
                    can_msgfd[i] for i in range(canfd_num)
                )

    def _recv_internal(self, timeout: Optional[float]) -> Tuple[Optional[can.Message], bool]:

        if self.rx_queue:
            return self._recv_from_queue()

        deadline = None
        while deadline is None or time.time() < deadline:
            if deadline is None and timeout is not None:
                deadline = time.time() + timeout

            self.poll_received_messages(timeout)

            if self.rx_queue:
                return self._recv_from_queue()

        return None, False

    def send(self, msg: can.Message, timeout: Optional[float] = None, sync: bool = True) -> None:
        msg = tosun_convert_msg(msg)
        self.device.transmit(msg, sync, timeout=timeout)

    @staticmethod
    def _detect_available_configs() -> List[can.typechecking.AutoDetectedConfig]:
        warnings.warn('Not supported by Tosun device.', DeprecationWarning, 2)

    def fileno(self) -> int:
        warnings.warn('Not supported by Tosun device.', DeprecationWarning, 2)

    # def cyclic_send(self, msg: can.Message, period: int):
    #     pass
    #
    # def del_cyclic_send(self, msg: can.Message):
    #     pass
    #
    # def configure_can_regs(self):
    #     self.device.tsapp_configure_can_register()

    def __enter__(self):
        self.device.connect()
        return self

    def shutdown(self) -> None:
        super().shutdown()
        self.device.finalize()


if __name__ == '__main__':
    from tosun import TSChannelIndex, TSAppChannelType, TSDeviceType, TSDeviceSubType
    import time
    mapping = {'app_name': 'TSMaster',
               'app_chl_idx': TSChannelIndex.CHN1,
               'app_chl_type': TSAppChannelType.APP_CAN,
               'hw_type': TSDeviceType.TS_USB_DEVICE,
               'hw_idx': 0,
               'hw_chl_idx': TSChannelIndex.CHN1,
               'hw_subtype': TSDeviceSubType.TC1016,
               'hw_name': 'TC1016'}
    with TosunBus([mapping, ], configs=[
            {'baudrate': 500_000, 'initenal_resistance': 1}
        ],
        # with_com=True
    ) as bus:
        # while True:
        #     print(bus.device.tsfifo_receive_msgs(0, 100, TSReadTxRxMode.TX_RX_MESSAGES, TSMasterMessageType.CAN))
        #     time.sleep(0.5)
        while True:
            print(bus.recv())
            time.sleep(0.01)




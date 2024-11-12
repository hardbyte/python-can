import can
from . import zlgcan
import logging
from typing import Optional, Dict, List
from can import BusABC
import threading
from queue import Queue, Empty
from can.exceptions import (
    CanInitializationError,
    CanInterfaceNotImplementedError,
    CanOperationError,
)


class CanIso:
    CAN_ISO = "0"
    CAN_NO_ISO = "1"


class CanMode:
    NORMAL = 0
    ONLY_LISTENING = 1


class TransmitType:
    NORMAL = 0  # Retry when fail
    ONCE = 1  # NO Retry when fail
    RECEIVE_OWN_MESSAGES = 2  # Retry when fail
    ONCE_RECEIVE_OWN_MESSAGES = 3  # NO Retry when fail


MAX_RCV_NUM = 1000

log = logging.getLogger("can.zlg")


def raise_can_operation_error(ret: int, message):
    if ret != zlgcan.ZCAN_STATUS_OK:
        raise CanOperationError(message)


class ZlgBus(BusABC):
    """
    The CAN Bus implemented for the Kvaser interface.
    """

    def __init__(
        self,
        channel: int,
        dev_type: int,
        fd: bool = False,
        bitrate: int = 500000,
        data_bitrate: int = 2000000,
        receive_own_messages: bool = False,
        filters: Optional[Dict] = None,
        retry_when_send_fail: bool = False,
        **kwargs,
    ):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param int dev_type:
            The dev_type is type of Can device.
        :param bool fd:
            If CAN-FD frames should be supported.

        :param int bitrate:
            Bitrate of channel in bit/s

        :param int data_bitrate:
            Which bitrate to use for data phase in CAN FD.
            Defaults to arbitration bitrate.

        :param bool driver_mode:
            Silent or normal.

        :param bool receive_own_messages:
            If messages transmitted should also be received back.
            Only works if single_handle is also False.
            If you want to receive messages from other applications on the same
            computer, set this to True or set single_handle to True.

        :param list filters:
            Filters to apply to the bus, it is dict, key include "is_extended/filter_start/filter_end".

        :param bool retry_when_send_fail:
            If the packet fails to be sent, resend the packet automatically.

        """
        self.channel = channel
        self.receive_own_messages = receive_own_messages
        self.retry_when_send_fail = retry_when_send_fail
        self.fd = fd
        self.queue_recv = Queue()
        self.queue_send = Queue()
        self.zcanlib = zlgcan.ZCAN()
        self.device_handle = self.zcanlib.OpenDevice(
            dev_type, 0, 0
        )  # 第二个参数是设备序号，默认0，只用第一个周立功
        if self.device_handle == zlgcan.INVALID_DEVICE_HANDLE:
            raise CanInitializationError(
                f"fail to get device handle, device type {dev_type}"
            ) from None
        # set bitrate
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, str(channel) + "/canfd_abit_baud_rate", str(bitrate).encode("utf-8")
        )
        raise_can_operation_error(
            ret, f"fail to set data_bitrate {data_bitrate} for channel {channel}"
        )
        if fd:
            # set canfd
            ret = self.zcanlib.ZCAN_SetValue(
                self.device_handle, str(channel) + "/canfd_standard", CanIso.CAN_ISO.encode("utf-8")
            )
            raise_can_operation_error(ret, f"fail to set canfd for channel {channel}")
            # set data_bitrate for canfd
            ret = self.zcanlib.ZCAN_SetValue(
                self.device_handle,
                str(channel) + "/canfd_dbit_baud_rate",
                str(data_bitrate).encode("utf-8"),
            )
            raise_can_operation_error(
                ret, f"fail to set data_bitrate {data_bitrate} for channel {channel}"
            )
            # merge can canfd
            ret = self.zcanlib.ZCAN_SetValue(
                self.device_handle, str(channel) + "/set_device_recv_merge", "1".encode("utf-8")
            )  # 0-单通道接收，1合并接收
            raise_can_operation_error(ret, f"set_device_recv_merge failed for channel {channel}!")
        chn_init_cfg = zlgcan.ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = zlgcan.ZCAN_TYPE_CANFD if fd else zlgcan.ZCAN_TYPE_CAN
        chn_init_cfg.config.canfd.mode = CanMode.NORMAL
        # init can channel
        self.chn_handle = self.zcanlib.InitCAN(self.device_handle, channel, chn_init_cfg)
        if self.chn_handle == 0 or self.chn_handle is None:
            raise CanOperationError(f"init CAN-Channel {channel} failed!")
        # set filter
        if filters:
            for filter in filters:
                self.__set_filter(filter)
            self.__ack_filters()
            self._is_filtered = True
        else:
            self._is_filtered = False
        # start can channel
        ret = self.zcanlib.StartCAN(self.chn_handle)
        raise_can_operation_error(ret, f"start CAN-Channel {channel} failed!")
        # thread event
        self.event_recv_send_batch_zlg = threading.Event()
        # start thread for recv
        threading.Thread(
            None, target=self.__recv_send_batch_zlg, args=(self.event_recv_send_batch_zlg,)
        ).start()
        super().__init__(
            channel=channel,
            **kwargs,
        )

    def __recv_send_batch_zlg(self, event):
        while not event.is_set():
            # 发送
            from ctypes import sizeof, memset

            send_size = self.queue_send.qsize()
            msgs: List[can.Message] = []
            for _ in range(send_size):
                msgs.append(self.queue_send.get())
            len_msgs = len(msgs)
            DataObj = (zlgcan.ZCANDataObj * len_msgs)()
            memset(DataObj, 0, sizeof(DataObj))
            for i in range(len_msgs):
                msg = msgs[i]
                data = self.__trans_data2zlg(msg.data, msg.dlc)
                DataObj[i].dataType = 1  # can报文
                DataObj[i].chnl = self.channel
                DataObj[i].zcanfddata.flag.frameType = 1 if msg.is_fd else 0  # 0-can,1-canfd
                DataObj[i].zcanfddata.flag.txDelay = 0  # 不添加延迟
                DataObj[i].zcanfddata.flag.txEchoRequest = 1  # 发送回显请求，0-不回显，1-回显
                if self.retry_when_send_fail:
                    DataObj[i].zcanfddata.flag.transmitType = TransmitType.NORMAL
                else:
                    DataObj[i].zcanfddata.flag.transmitType = TransmitType.ONCE
                DataObj[i].zcanfddata.frame.eff = (
                    1 if msg.is_extended_id else 0
                )  # 0-标准帧，1-扩展帧
                DataObj[i].zcanfddata.frame.rtr = (
                    1 if msg.is_remote_frame else 0
                )  # 0-数据帧，1-远程帧
                DataObj[i].zcanfddata.frame.can_id = msg.arbitration_id
                DataObj[i].zcanfddata.frame.len = msg.dlc
                if msg.is_fd:
                    DataObj[i].zcanfddata.frame.brs = (
                        1 if msg.bitrate_switch else 0
                    )  # BRS 加速标志位：0不加速，1加速
                for j in range(DataObj[i].zcanfddata.frame.len):
                    DataObj[i].zcanfddata.frame.data[j] = data[j]
            ret = self.zcanlib.TransmitData(self.device_handle, DataObj, len_msgs)
            log.debug(f"Tranmit Num: {ret}.")
            # 接收
            rcv_num = self.zcanlib.GetReceiveNum(self.chn_handle, zlgcan.ZCAN_TYPE_MERGE)
            if rcv_num:
                read_cnt = MAX_RCV_NUM if rcv_num >= MAX_RCV_NUM else rcv_num
                msgs_zlg, read_cnt = self.zcanlib.ReceiveData(self.device_handle, read_cnt)
                for i in range(read_cnt):
                    msg_zlg = msgs_zlg[i]
                    if msg_zlg.dataType != 1:  # 筛选出can报文
                        continue
                    msg = can.Message(
                        is_fd=bool(msg_zlg.zcanfddata.flag.frameType),
                        timestamp=float(msg_zlg.zcanfddata.timestamp) / 1000000,
                        is_extended_id=bool(msg_zlg.zcanfddata.frame.eff),
                        arbitration_id=msg_zlg.zcanfddata.frame.can_id,
                        data=[
                            msg_zlg.zcanfddata.frame.data[j]
                            for j in range(msg_zlg.zcanfddata.frame.len)
                        ],
                        dlc=msg_zlg.zcanfddata.frame.len,
                        channel=self.channel,
                        is_remote_frame=bool(msg_zlg.zcanfddata.frame.rtr),
                        is_rx=False if msg_zlg.zcanfddata.flag.txEchoed else True,
                    )
                    self.queue_recv.put(msg)
            event.wait(timeout=0.005)

    def add_filters(self, filters: Optional[Dict]):
        if filters is None:
            return
        for filter in filters:
            self.__set_filter(filter)
        self.__ack_filters()
        self._is_filtered = True

    def __set_filter(self, filter: Dict):
        # 0 standard/1 extended
        is_extended = filter["is_extended"]
        filter_start = filter["filter_start"]
        filter_end = filter["filter_end"]
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, str(self.channel) + "/filter_mode", str(is_extended).encode("utf-8")
        )  # 扩展帧滤波
        raise_can_operation_error(ret, f"Set CH{self.channel} filter_mode failed!")
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle,
            str(self.channel) + "/filter_start",
            hex(filter_start).encode("utf-8"),
        )
        raise_can_operation_error(ret, f"Set CH{self.channel}  filter_start failed!")
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, str(self.channel) + "/filter_end", hex(filter_end).encode("utf-8")
        )
        raise_can_operation_error(ret, f"Set CH{self.channel}  filter_end failed!")

    def __ack_filters(self):
        ret = self.zcanlib.ZCAN_SetValue(
            self.device_handle, str(self.channel) + "/filter_ack", "0".encode("utf-8")
        )
        raise_can_operation_error(ret, f"Set CH{self.channel} filter_ack failed!")

    def flush_tx_buffer(self):
        raise CanInterfaceNotImplementedError("flush_tx_buffer is not implemented")

    def _recv_internal(self, timeout=None):
        try:
            msg = self.queue_recv.get(block=True, timeout=timeout)
        except Empty:
            return None, self._is_filtered
        else:
            return msg, self._is_filtered

    @staticmethod
    def __trans_data2zlg(data, dlc: int):
        if isinstance(data, int):
            data = data.to_bytes(length=dlc, byteorder="big")
        elif isinstance(data, bytearray) or isinstance(data, bytes):
            data = data
        else:
            data = list(data)
        return data

    def send(self, msg: can.Message, timeout=None):
        self.queue_send.put(msg)

    def shutdown(self):
        self.event_recv_send_batch_zlg.set()
        # Close CAN
        ret = self.zcanlib.ResetCAN(self.chn_handle)
        if ret == 1:
            log.debug("Close CAN successfully.")
        # Close Device
        ret = self.zcanlib.CloseDevice(self.device_handle)
        if ret == 1:
            log.debug("Close Device success! ")

    @staticmethod
    def _detect_available_configs():
        zcanlib = zlgcan.ZCAN()
        handle = zcanlib.OpenDevice(zlgcan.ZCAN_USBCANFD_MINI, 0, 0)
        if handle == zlgcan.INVALID_DEVICE_HANDLE:
            return []
        info: str = str(zcanlib.GetDeviceInf(handle))
        zcanlib.CloseDevice(handle)
        param: Dict = {
            line_.split(":", 1)[0]: line_.split(":", 1)[1] for line_ in info.splitlines()
        }
        dev_type_name: str = param.get("Hardware Type", None)
        if "USBCAN" not in dev_type_name:
            return []
        dev_type_var_name: str = f'ZCAN_{dev_type_name.replace("-", "_")}'
        dev_type: int = eval(f"zlgcan.{dev_type_var_name}")
        chn_num = int(param.get("CAN Number", None))
        fd = "CANFD" in dev_type_name.upper()
        serial = param.get("Serial", None)
        return [
            dict(
                interface="zlg",
                dev_type_name=dev_type_name,
                dev_type=dev_type,
                channel=i,
                fd=fd,
                serial=serial,
            )
            for i in range(chn_num)
        ]

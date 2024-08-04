"""
The ZLGCAN device supported based on zlgcan-driver-rs.
See the example `zlgcan_demo.py`
"""
import can
import collections
import time

from can import CanError, CanInitializationError, Message
from can.bus import LOG

from typing import Optional, Union, Sequence, Deque, Tuple, List, Dict
try:
    from zlgcan_driver_py import ZCanChlCfgPy, ZCanMessagePy, ZDeriveInfoPy, ZCanChlCfgFactoryWrap, ZCanDriverWrap, \
        convert_to_python, convert_from_python, set_message_mode, zlgcan_cfg_factory_can, zlgcan_open, \
        zlgcan_device_info, zlgcan_init_can, zlgcan_clear_can_buffer, zlgcan_send, zlgcan_recv, zlgcan_close
except ModuleNotFoundError:
    import sys
    import platform
    _system_bit, _ = platform.architecture()
    _platform = sys.platform
    not_support = CanError(f"The system {_platform}'.'{_system_bit} is not supported!")
    require_lib = CanError("Please install library `zlgcan-driver-py`!")
    raise {
        "win32": {"32bit": not_support}.get(_system_bit, require_lib),
        "darwin": not_support,
        "linux": {"32bit": not_support}.get(_system_bit, require_lib)
    }.get(_platform, not_support)


class ZCanTxMode:
    NORMAL = 0  # 正常发送
    SINGLE = 1  # 单次发送
    SELF_SR = 2  # 自发自收
    SINGLE_SELF_SR = 3  # 单次自发自收


class ZCANDeviceType:
    ZCAN_PCI5121 = 1
    ZCAN_PCI9810 = 2
    ZCAN_USBCAN1 = 3
    ZCAN_USBCAN2 = 4
    ZCAN_PCI9820 = 5
    ZCAN_CAN232 = 6
    ZCAN_PCI5110 = 7
    ZCAN_CANLITE = 8
    ZCAN_ISA9620 = 9
    ZCAN_ISA5420 = 10
    ZCAN_PC104CAN = 11
    ZCAN_CANETUDP = 12
    ZCAN_CANETE = 12
    ZCAN_DNP9810 = 13
    ZCAN_PCI9840 = 14
    ZCAN_PC104CAN2 = 15
    ZCAN_PCI9820I = 16
    ZCAN_CANETTCP = 17
    ZCAN_PCIE_9220 = 18
    ZCAN_PCI5010U = 19
    ZCAN_USBCAN_E_U = 20
    ZCAN_USBCAN_2E_U = 21
    ZCAN_PCI5020U = 22
    ZCAN_EG20T_CAN = 23
    ZCAN_PCIE9221 = 24
    ZCAN_WIFICAN_TCP = 25
    ZCAN_WIFICAN_UDP = 26
    ZCAN_PCIe9120 = 27
    ZCAN_PCIe9110 = 28
    ZCAN_PCIe9140 = 29
    ZCAN_USBCAN_4E_U = 31
    ZCAN_CANDTU_200UR = 32
    ZCAN_CANDTU_MINI = 33
    ZCAN_USBCAN_8E_U = 34
    ZCAN_CANREPLAY = 35
    ZCAN_CANDTU_NET = 36
    ZCAN_CANDTU_100UR = 37
    ZCAN_PCIE_CANFD_100U = 38
    ZCAN_PCIE_CANFD_200U = 39
    ZCAN_PCIE_CANFD_400U = 40
    ZCAN_USBCANFD_200U = 41
    ZCAN_USBCANFD_100U = 42
    ZCAN_USBCANFD_MINI = 43
    ZCAN_CANFDCOM_100IE = 44
    ZCAN_CANSCOPE = 45
    ZCAN_CLOUD = 46
    ZCAN_CANDTU_NET_400 = 47
    ZCAN_CANFDNET_TCP = 48
    ZCAN_CANFDNET_200U_TCP = 48
    ZCAN_CANFDNET_UDP = 49
    ZCAN_CANFDNET_200U_UDP = 49
    ZCAN_CANFDWIFI_TCP = 50
    ZCAN_CANFDWIFI_100U_TCP = 50
    ZCAN_CANFDWIFI_UDP = 51
    ZCAN_CANFDWIFI_100U_UDP = 51
    ZCAN_CANFDNET_400U_TCP = 52
    ZCAN_CANFDNET_400U_UDP = 53
    ZCAN_CANFDBLUE_200U = 54
    ZCAN_CANFDNET_100U_TCP = 55
    ZCAN_CANFDNET_100U_UDP = 56
    ZCAN_CANFDNET_800U_TCP = 57
    ZCAN_CANFDNET_800U_UDP = 58
    ZCAN_USBCANFD_800U = 59
    ZCAN_PCIE_CANFD_100U_EX = 60
    ZCAN_PCIE_CANFD_400U_EX = 61
    ZCAN_PCIE_CANFD_200U_MINI = 62
    ZCAN_PCIE_CANFD_200U_M2 = 63
    ZCAN_CANFDDTU_400_TCP = 64
    ZCAN_CANFDDTU_400_UDP = 65
    ZCAN_CANFDWIFI_200U_TCP = 66
    ZCAN_CANFDWIFI_200U_UDP = 67
    ZCAN_CANFDDTU_800ER_TCP = 68
    ZCAN_CANFDDTU_800ER_UDP = 69
    ZCAN_CANFDDTU_800EWGR_TCP = 70
    ZCAN_CANFDDTU_800EWGR_UDP = 71
    ZCAN_CANFDDTU_600EWGR_TCP = 72
    ZCAN_CANFDDTU_600EWGR_UDP = 73

    ZCAN_OFFLINE_DEVICE = 98
    ZCAN_VIRTUAL_DEVICE = 99


class ZCanBus(can.BusABC):

    def __init__(self,
                 channel: Union[int, Sequence[int], str] = None, *,
                 device_type: int,
                 device_index: int = 0,
                 derive: ZDeriveInfoPy = None,
                 rx_queue_size: Optional[int] = None,
                 configs: Union[List[Dict], Tuple[Dict]] = None,
                 can_filters: Optional[can.typechecking.CanFilters] = None,
                 **kwargs: object):
        """
        Constructor

        :param channel: Not used(from super).
        :param device_type: The device type that your device belongs, see `ZCANDeviceType`.
        :param device_index: The device index.
        :param derive: The deriver info for specifying the channels and canfd supported if your device is not official.
        :param rx_queue_size: The receiving queue size.
        :param configs: The channel configration. See `zlgcan_demo.py`.
        :param can_filters: From super.
        """
        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

        try:
            cfg_length = len(configs)
            if cfg_length == 0:
                raise CanInitializationError("ZLG-CAN - Configuration list or tuple of dict is required.")

            self.rx_queue = collections.deque(
                maxlen=rx_queue_size
            )  # type: Deque[can.Message]               # channel, raw_msg
            self.channels = []

            factory = zlgcan_cfg_factory_can()
            self.device = zlgcan_open(device_type, device_index, derive)

            self.dev_info = zlgcan_device_info(self.device)
            if self.dev_info is not None:
                LOG.info(f"Device: {self.dev_info} has opened")

            cfg_list = []
            for idx, cfg in enumerate(configs):
                bitrate = cfg.get("bitrate", None)
                assert bitrate is not None, "bitrate is required!"
                _cfg = ZCanChlCfgPy(
                    dev_type=device_type,
                    chl_type=cfg.get("chl_type", 0),
                    chl_mode=cfg.get("chl_mode", 0),
                    bitrate=bitrate,
                    filter=cfg.get("filter"),
                    dbitrate=cfg.get("dbitrate"),
                    resistance=bool(cfg.get("resistance", 1)),
                    acc_code=cfg.get("acc_code"),
                    acc_mask=cfg.get("acc_mask"),
                    brp=cfg.get("brp")
                )
                cfg_list.append(_cfg)
                self.channels.append(idx)

            zlgcan_init_can(self.device, factory, cfg_list)
        except Exception as e:
            self.shutdown()
            raise e

    def send(self, msg: can.Message, timeout: Optional[float] = None, *,
             tx_mode: ZCanTxMode = ZCanTxMode.NORMAL) -> None:
        raw_msg = convert_from_python(msg)
        set_message_mode(raw_msg, tx_mode)
        zlgcan_send(self.device, raw_msg)

    def shutdown(self) -> None:
        LOG.debug("ZLG-CAN - shutdown.")
        super().shutdown()
        if hasattr(self, "device"):
            zlgcan_close(self.device)

    def poll_received_messages(self, timeout):
        for channel in self.channels:
            raw_msgs: list[ZCanMessagePy] = zlgcan_recv(self.device, channel, timeout)
            # for raw_msg in raw_msgs:
            #     self.rx_queue.append(convert_to_python(raw_msg))
            self.rx_queue.extend(map(lambda raw_msg: convert_to_python(raw_msg), raw_msgs))

    def _recv_from_queue(self) -> Tuple[Message, bool]:
        """Return a message from the internal receive queue"""
        msg = self.rx_queue.popleft()
        return msg, False

    def _recv_internal(
            self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:
        if self.rx_queue:
            return self._recv_from_queue()

        deadline = None
        while deadline is None or time.monotonic() < deadline:
            if deadline is None and timeout is not None:
                deadline = time.monotonic() + timeout

            self.poll_received_messages(timeout or 0)

            if self.rx_queue:
                return self._recv_from_queue()

        return None, False


with ZCanBus(interface="zlgcan", device_type=ZCANDeviceType.ZCAN_USBCANFD_200U,
             configs=[{'bitrate': 500000, 'resistance': 1}, {'bitrate': 1000000, 'resistance': 1}]) as bus:
    # bus.send(can.Message(
    #     arbitration_id=0x7DF,
    #     is_extended_id=False,
    #     channel=0,
    #     data=[0x02, 0x10, 0x03, ],
    #     dlc=3,
    # ), tx_mode=ZCanTxMode.SELF_SR)

    start = time.monotonic()
    while time.monotonic() - start < 5:
        _msg = bus.recv()
        print(_msg)


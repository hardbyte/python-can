"""
The ZLGCAN device supported based on zlgcan-driver-rs.
See the example `zlgcan_demo.py`
"""
import time

import can
import collections
import os
import platform
import sys

from ctypes import c_uint8, c_bool, c_int64, c_int32, c_char_p, cdll, c_void_p, byref, c_uint32, POINTER, Structure, \
    string_at, cast
from typing import Optional, Union, Sequence, Deque, Tuple, List, Dict

from can import CanError, CanInitializationError, Message
from can.bus import LOG


class ZCanTxMode:
    NORMAL = 0              # 正常发送
    SINGLE = 1              # 单次发送
    SELF_SR = 2             # 自发自收
    SINGLE_SELF_SR = 3      # 单次自发自收


class ZCANDeviceType:
    ZCAN_PCI5121                       = 1
    ZCAN_PCI9810                       = 2
    ZCAN_USBCAN1                       = 3
    ZCAN_USBCAN2                       = 4
    ZCAN_PCI9820                       = 5
    ZCAN_CAN232                        = 6
    ZCAN_PCI5110                       = 7
    ZCAN_CANLITE                       = 8
    ZCAN_ISA9620                       = 9
    ZCAN_ISA5420                       = 10
    ZCAN_PC104CAN                      = 11
    ZCAN_CANETUDP                      = 12
    ZCAN_CANETE                        = 12
    ZCAN_DNP9810                       = 13
    ZCAN_PCI9840                       = 14
    ZCAN_PC104CAN2                     = 15
    ZCAN_PCI9820I                      = 16
    ZCAN_CANETTCP                      = 17
    ZCAN_PCIE_9220                     = 18
    ZCAN_PCI5010U                      = 19
    ZCAN_USBCAN_E_U                    = 20
    ZCAN_USBCAN_2E_U                   = 21
    ZCAN_PCI5020U                      = 22
    ZCAN_EG20T_CAN                     = 23
    ZCAN_PCIE9221                      = 24
    ZCAN_WIFICAN_TCP                   = 25
    ZCAN_WIFICAN_UDP                   = 26
    ZCAN_PCIe9120                      = 27
    ZCAN_PCIe9110                      = 28
    ZCAN_PCIe9140                      = 29
    ZCAN_USBCAN_4E_U                   = 31
    ZCAN_CANDTU_200UR                  = 32
    ZCAN_CANDTU_MINI                   = 33
    ZCAN_USBCAN_8E_U                   = 34
    ZCAN_CANREPLAY                     = 35
    ZCAN_CANDTU_NET                    = 36
    ZCAN_CANDTU_100UR                  = 37
    ZCAN_PCIE_CANFD_100U               = 38
    ZCAN_PCIE_CANFD_200U               = 39
    ZCAN_PCIE_CANFD_400U               = 40
    ZCAN_USBCANFD_200U                 = 41
    ZCAN_USBCANFD_100U                 = 42
    ZCAN_USBCANFD_MINI                 = 43
    ZCAN_CANFDCOM_100IE                = 44
    ZCAN_CANSCOPE                      = 45
    ZCAN_CLOUD                         = 46
    ZCAN_CANDTU_NET_400                = 47
    ZCAN_CANFDNET_TCP                  = 48
    ZCAN_CANFDNET_200U_TCP             = 48
    ZCAN_CANFDNET_UDP                  = 49
    ZCAN_CANFDNET_200U_UDP             = 49
    ZCAN_CANFDWIFI_TCP                 = 50
    ZCAN_CANFDWIFI_100U_TCP            = 50
    ZCAN_CANFDWIFI_UDP                 = 51
    ZCAN_CANFDWIFI_100U_UDP            = 51
    ZCAN_CANFDNET_400U_TCP             = 52
    ZCAN_CANFDNET_400U_UDP             = 53
    ZCAN_CANFDBLUE_200U                = 54
    ZCAN_CANFDNET_100U_TCP             = 55
    ZCAN_CANFDNET_100U_UDP             = 56
    ZCAN_CANFDNET_800U_TCP             = 57
    ZCAN_CANFDNET_800U_UDP             = 58
    ZCAN_USBCANFD_800U                 = 59
    ZCAN_PCIE_CANFD_100U_EX            = 60
    ZCAN_PCIE_CANFD_400U_EX            = 61
    ZCAN_PCIE_CANFD_200U_MINI          = 62
    ZCAN_PCIE_CANFD_200U_M2            = 63
    ZCAN_CANFDDTU_400_TCP              = 64
    ZCAN_CANFDDTU_400_UDP              = 65
    ZCAN_CANFDWIFI_200U_TCP            = 66
    ZCAN_CANFDWIFI_200U_UDP            = 67
    ZCAN_CANFDDTU_800ER_TCP            = 68
    ZCAN_CANFDDTU_800ER_UDP            = 69
    ZCAN_CANFDDTU_800EWGR_TCP          = 70
    ZCAN_CANFDDTU_800EWGR_UDP          = 71
    ZCAN_CANFDDTU_600EWGR_TCP          = 72
    ZCAN_CANFDDTU_600EWGR_UDP          = 73

    ZCAN_OFFLINE_DEVICE                = 98
    ZCAN_VIRTUAL_DEVICE                = 99


class ZCanDeriveInfo(Structure):
    _fields_ = [("canfd", c_bool),
                ("channels", c_uint8),
                ]


class ZCanChlCfgFactory(Structure):
    pass


class ZCanChlCfg(Structure):
    _fields_ = [("dev_type", c_uint32),
                ("chl_type", c_uint8),
                ("chl_mode", c_uint8),
                ("bitrate", c_uint32),
                ("filter", c_char_p),
                ("dbitrate", POINTER(c_uint32)),
                ("resistance", POINTER(c_bool)),
                ("acc_code", POINTER(c_uint32)),
                ("acc_mask", POINTER(c_uint32)),
                ("brp", POINTER(c_uint32)),
                ]


class CanMessage(Structure):
    _fields_ = [("timestamp", c_int64),
                ("arbitration_id", c_int32),
                ("is_extended_id", c_bool),
                ("is_remote_frame", c_bool),
                ("is_error_frame", c_bool),
                ("channel", c_uint8),
                ("len", c_uint8),
                ("data", c_char_p),
                ("is_fd", c_bool),
                ("is_rx", c_bool),
                ("bitrate_switch", c_bool),
                ("error_state_indicator", c_bool),
                ("tx_mode", c_uint8)
                ]


_current_path = os.path.dirname(__file__)
_system_bit, _ = platform.architecture()
_PREFIX = {"win32": ""}.get(sys.platform, "lib")
_EXTEND = {"darwin": "dylib", "win32": "dll"}.get(sys.platform, "so")
_PRE_EXTEND = "x86_64" if _system_bit == "64bit" else "x86"
_LIB_PATH = os.path.join(_current_path, f"{_PREFIX}zlgcan_driver_rs_api.{_PRE_EXTEND}.{_EXTEND}")
if not os.path.exists(_LIB_PATH):
    raise CanError(
        message=f"The library is required!\n"
                f"1. Download the base library and configration file from "
                f"`https://github.com/zhuyu4839/zlgcan-driver-rs`.\n"
                f"  Copy the `bitrate.cfg.yaml` and `zlgcan-driver-rs/zlgcan-driver/library` into your project.\n"
                f"2. Download the library named `zlgcan-driver-rs-api.tar.gz` "
                f"from `https://github.com/zhuyu4839/zlgcan-driver-rs/releases`.\n"
                f"  Unpack the library file depends on your python arch and copy them to `{_current_path}`!\n"
                f"Ensure your project like this:\n"
                f"  - demo\n"
                f"    - main.py\n"
                f"    - bitrate.cfg.yaml\n"
                f"    - library\n"
                f"      - ...")
_LIB = cdll.LoadLibrary(_LIB_PATH)
_LIB.zlgcan_open.restype = c_void_p
_LIB.zlgcan_device_info.restype = c_char_p
_LIB.zlgcan_cfg_factory_can.restype = POINTER(ZCanChlCfgFactory)
_LIB.zlgcan_chl_cfg_can.restype = c_void_p
_LIB.zlgcan_recv.argtypes = [c_void_p, c_uint8, c_uint32, POINTER(POINTER(CanMessage)), POINTER(c_char_p)]


class ZCanBus(can.BusABC):

    def __init__(self,
                 channel: Union[int, Sequence[int], str] = None, *,
                 device_type: int,
                 device_index: int = 0,
                 derive: ZCanDeriveInfo = None,
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

        cfg_length = len(configs)
        if cfg_length == 0:
            raise CanInitializationError("ZLG-CAN - Configuration list or tuple of dict is required.")

        self.rx_queue = collections.deque(
            maxlen=rx_queue_size
        )  # type: Deque[can.Message]               # channel, raw_msg
        self.channels = []

        error = c_char_p()

        factory = _LIB.zlgcan_cfg_factory_can(byref(error))
        if not factory:
            raise can.CanOperationError(error.value.decode("utf-8"))
            
        if derive is None:
            derive = c_void_p(0)
        else:
            derive = byref(derive)
        device = _LIB.zlgcan_open(device_type, device_index, derive, byref(error))
        if not device:
            raise can.CanOperationError(error.value.decode("utf-8"))
        self.device = c_void_p(device)

        self.dev_info = _LIB.zlgcan_device_info(self.device, byref(error))
        if self.dev_info is not None:
            LOG.info(f"Device: {self.dev_info.decode('utf-8')} has opened")

        try:
            cfg_ptrs = (c_void_p * cfg_length)()
            for idx, cfg in enumerate(configs):
                bitrate = cfg.get("bitrate", None)
                assert bitrate is not None, "bitrate is required!"
                filter = cfg.get("filter")
                dbitrate = cfg.get("dbitrate")
                resistance = cfg.get("resistance")
                acc_code = cfg.get("acc_code")
                acc_mask = cfg.get("acc_mask")
                brp = cfg.get("brp")
                _cfg = ZCanChlCfg()
                _cfg.dev_type = device_type
                _cfg.chl_type = cfg.get("chl_type", 0)
                _cfg.chl_mode = cfg.get("chl_mode", 0)
                _cfg.bitrate = bitrate
                _cfg.filter = None if filter is None else cast(id(filter), POINTER(c_uint8))
                _cfg.dbitrate = None if dbitrate is None else cast(id(dbitrate), POINTER(c_uint32))
                _cfg.resistance = None if resistance is None else cast(id(resistance), POINTER(c_bool))
                _cfg.acc_code = None if acc_code is None else cast(id(acc_code), POINTER(c_uint32))
                _cfg.acc_mask = None if acc_mask is None else cast(id(acc_mask), POINTER(c_uint32))
                _cfg.brp = None if brp is None else cast(id(brp), POINTER(c_uint32))
                cfg_ptr = _LIB.zlgcan_chl_cfg_can(factory, _cfg, byref(error))
                if not cfg_ptr:
                    raise can.CanOperationError(error.value.decode("utf-8"))
                cfg_ptrs[idx] = cfg_ptr
                self.channels.append(idx)

            ret = _LIB.zlgcan_init_can(self.device, byref(cfg_ptrs), cfg_length, byref(error))
            if not ret:
                raise can.CanOperationError(error.value.decode("utf-8"))
        except Exception as e:
            self.shutdown()
            raise e

    def send(self, msg: can.Message, timeout: Optional[float] = None, *, tx_mode: ZCanTxMode = ZCanTxMode.NORMAL) -> None:
        raw_msg = CanMessage()
        raw_msg.timestamp = int(msg.timestamp * 1000)
        raw_msg.arbitration_id = msg.arbitration_id
        raw_msg.is_extended_id = msg.is_extended_id
        raw_msg.is_remote_frame = msg.is_remote_frame
        raw_msg.is_error_frame = msg.is_error_frame
        raw_msg.channel = msg.channel
        raw_msg.len = msg.dlc
        raw_msg.data = c_char_p(bytes(msg.data))
        raw_msg.is_fd = msg.is_fd
        raw_msg.bitrate_switch = msg.bitrate_switch
        raw_msg.error_state_indicator = msg.error_state_indicator
        raw_msg.tx_mode = tx_mode
        error = c_char_p()
        ret = _LIB.zlgcan_send(self.device, raw_msg, byref(error))
        if not ret:
            LOG.warning("Send message failed: {}", error.value.decode("utf-8"))

    def shutdown(self) -> None:
        LOG.debug("ZLG-CAN - shutdown.")
        super().shutdown()
        if hasattr(self, "device"):
            _LIB.zlgcan_close(self.device)

    def poll_received_messages(self, timeout):
        for channel in self.channels:
            error = c_char_p()
            buffer = cast(c_void_p(0), POINTER(CanMessage))
            count = _LIB.zlgcan_recv(self.device, channel, timeout, byref(buffer), byref(error))
            if count == 0:
                if error.value is not None:
                    LOG.warning(error.value.decode("utf-8"))

            for i in range(count):
                raw_msg = buffer[i]
                msg = can.Message(
                    timestamp=raw_msg.timestamp / 1000.,
                    arbitration_id=raw_msg.arbitration_id,
                    is_extended_id=raw_msg.is_extended_id,
                    is_remote_frame=raw_msg.is_remote_frame,
                    is_error_frame=raw_msg.is_error_frame,
                    channel=raw_msg.channel,
                    dlc=raw_msg.len,
                    data=string_at(raw_msg.data, raw_msg.len),
                    is_fd=raw_msg.is_fd,
                    bitrate_switch=raw_msg.bitrate_switch,
                    error_state_indicator=raw_msg.error_state_indicator,
                )
                self.rx_queue.append(msg)

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


if __name__ == "__main__":
    with ZCanBus(device_type=ZCANDeviceType.ZCAN_USBCANFD_200U,
                 configs=[{"bitrate": 500_000}, {"bitrate": 500_000}]) as bus:
        while True:
            bus.send(can.Message(
                arbitration_id=0x123,
                is_extended_id=False,
                channel=0,
                data=[0x01, 0x02, 0x03, ],
                dlc=3,
            ))

            # time.sleep(0.1)
            _msg = bus.recv()
            print(_msg)



"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems.

Authors: Julien Grave <grave.jul@gmail.com>, Christian Sandberg
"""

# Import Standard Python Modules
# ==============================
import ctypes
import logging
import time
import os
from types import ModuleType
from typing import (
    List,
    NamedTuple,
    Optional,
    Tuple,
    Sequence,
    Union,
    Any,
    Dict,
    Callable,
)

WaitForSingleObject: Optional[Callable[[int, int], int]]
INFINITE: Optional[int]
try:
    # Try builtin Python 3 Windows API
    from _winapi import WaitForSingleObject, INFINITE

    HAS_EVENTS = True
except ImportError:
    WaitForSingleObject, INFINITE = None, None
    HAS_EVENTS = False

# Import Modules
# ==============
from can import BusABC, Message, CanInterfaceNotImplementedError, CanInitializationError
from can.util import (
    len2dlc,
    dlc2len,
    deprecated_args_alias,
    time_perfcounter_correlation,
)
from can.typechecking import AutoDetectedConfig, CanFilters, Channel

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Import Vector API modules
# =========================
from .exceptions import VectorError, VectorInitializationError, VectorOperationError
from . import xldefine, xlclass

# Import safely Vector API module for Travis tests
xldriver: Optional[ModuleType] = None
try:
    from . import xldriver
except Exception as exc:
    LOG.warning("Could not import vxlapi: %s", exc)


class VectorBus(BusABC):
    """The CAN Bus implemented for the Vector interface."""

    deprecated_args = dict(
        sjwAbr="sjw_abr",
        tseg1Abr="tseg1_abr",
        tseg2Abr="tseg2_abr",
        sjwDbr="sjw_dbr",
        tseg1Dbr="tseg1_dbr",
        tseg2Dbr="tseg2_dbr",
    )

    @deprecated_args_alias(**deprecated_args)
    def __init__(
        self,
        channel: Union[int, Sequence[int], str],
        can_filters: Optional[CanFilters] = None,
        poll_interval: float = 0.01,
        receive_own_messages: bool = False,
        bitrate: Optional[int] = None,
        rx_queue_size: int = 2 ** 14,
        app_name: Optional[str] = "CANalyzer",
        serial: Optional[int] = None,
        fd: bool = False,
        data_bitrate: Optional[int] = None,
        sjw_abr: int = 2,
        tseg1_abr: int = 6,
        tseg2_abr: int = 3,
        sjw_dbr: int = 2,
        tseg1_dbr: int = 6,
        tseg2_dbr: int = 3,
        **kwargs: Any,
    ) -> None:
        """
        :param channel:
            The channel indexes to create this bus with.
            Can also be a single integer or a comma separated string.
        :param can_filters:
            See :class:`can.BusABC`.
        :param receive_own_messages:
            See :class:`can.BusABC`.
        :param poll_interval:
            Poll interval in seconds.
        :param bitrate:
            Bitrate in bits/s.
        :param rx_queue_size:
            Number of messages in receive queue (power of 2).
            CAN: range `16…32768`
            CAN-FD: range `8192…524288`
        :param app_name:
            Name of application in *Vector Hardware Config*.
            If set to `None`, the channel should be a global channel index.
        :param serial:
            Serial number of the hardware to be used.
            If set, the channel parameter refers to the channels ONLY on the specified hardware.
            If set, the `app_name` does not have to be previously defined in
            *Vector Hardware Config*.
        :param fd:
            If CAN-FD frames should be supported.
        :param data_bitrate:
            Which bitrate to use for data phase in CAN FD.
            Defaults to arbitration bitrate.
        :param sjw_abr:
            Bus timing value sample jump width (arbitration).
        :param tseg1_abr:
            Bus timing value tseg1 (arbitration)
        :param tseg2_abr:
            Bus timing value tseg2 (arbitration)
        :param sjw_dbr:
            Bus timing value sample jump width (data)
        :param tseg1_dbr:
            Bus timing value tseg1 (data)
        :param tseg2_dbr:
            Bus timing value tseg2 (data)

        :raise can.CanInterfaceNotImplementedError:
            If the current operating system is not supported or the driver could not be loaded.
        :raise can.CanInitializationError:
            If the bus could not be set up.
            This may or may not be a :class:`can.interfaces.vector.VectorInitializationError`.
        """
        if os.name != "nt" and not kwargs.get("_testing", False):
            raise CanInterfaceNotImplementedError(
                f"The Vector interface is only supported on Windows, "
                f'but you are running "{os.name}"'
            )

        if xldriver is None:
            raise CanInterfaceNotImplementedError("The Vector API has not been loaded")
        self.xldriver = xldriver  # keep reference so mypy knows it is not None

        self.poll_interval = poll_interval

        self.channels: Sequence[int]
        if isinstance(channel, int):
            self.channels = [channel]
        elif isinstance(channel, str):  # must be checked before generic Sequence
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(",")]
        elif isinstance(channel, Sequence):
            self.channels = [int(ch) for ch in channel]
        else:
            raise TypeError(
                f"Invalid type for channels parameter: {type(channel).__name__}"
            )

        self._app_name = app_name.encode() if app_name is not None else b""
        self.channel_info = "Application %s: %s" % (
            app_name,
            ", ".join(f"CAN {ch + 1}" for ch in self.channels),
        )

        if serial is not None:
            app_name = None
            channel_index = []
            channel_configs = get_channel_configs()
            for channel_config in channel_configs:
                if channel_config.serialNumber == serial:
                    if channel_config.hwChannel in self.channels:
                        channel_index.append(channel_config.channelIndex)
            if channel_index:
                if len(channel_index) != len(self.channels):
                    LOG.info(
                        "At least one defined channel wasn't found on the specified hardware."
                    )
                self.channels = channel_index
            else:
                # Is there any better way to raise the error?
                raise CanInitializationError(
                    "None of the configured channels could be found on the specified hardware."
                )

        self.xldriver.xlOpenDriver()
        self.port_handle = xlclass.XLportHandle(xldefine.XL_INVALID_PORTHANDLE)
        self.mask = 0
        self.fd = fd
        # Get channels masks
        self.channel_masks: Dict[Optional[Channel], int] = {}
        self.index_to_channel = {}

        for channel in self.channels:
            if app_name:
                # Get global channel index from application channel
                hw_type, hw_index, hw_channel = self.get_application_config(
                    app_name, channel
                )
                LOG.debug("Channel index %d found", channel)
                idx = self.xldriver.xlGetChannelIndex(hw_type, hw_index, hw_channel)
                if idx < 0:
                    # Undocumented behavior! See issue #353.
                    # If hardware is unavailable, this function returns -1.
                    # Raise an exception as if the driver
                    # would have signalled XL_ERR_HW_NOT_PRESENT.
                    raise VectorInitializationError(
                        xldefine.XL_Status.XL_ERR_HW_NOT_PRESENT,
                        xldefine.XL_Status.XL_ERR_HW_NOT_PRESENT.name,
                        "xlGetChannelIndex",
                    )
            else:
                # Channel already given as global channel
                idx = channel
            mask = 1 << idx
            self.channel_masks[channel] = mask
            self.index_to_channel[idx] = channel
            self.mask |= mask

        permission_mask = xlclass.XLaccess()
        # Set mask to request channel init permission if needed
        if bitrate or fd:
            permission_mask.value = self.mask
        if fd:
            self.xldriver.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                permission_mask,
                rx_queue_size,
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4,
                xldefine.XL_BusTypes.XL_BUS_TYPE_CAN,
            )
        else:
            self.xldriver.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                permission_mask,
                rx_queue_size,
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION,
                xldefine.XL_BusTypes.XL_BUS_TYPE_CAN,
            )
        LOG.debug(
            "Open Port: PortHandle: %d, PermissionMask: 0x%X",
            self.port_handle.value,
            permission_mask.value,
        )

        if permission_mask.value == self.mask:
            if fd:
                self.canFdConf = xlclass.XLcanFdConf()
                if bitrate:
                    self.canFdConf.arbitrationBitRate = int(bitrate)
                else:
                    self.canFdConf.arbitrationBitRate = 500000
                self.canFdConf.sjwAbr = int(sjw_abr)
                self.canFdConf.tseg1Abr = int(tseg1_abr)
                self.canFdConf.tseg2Abr = int(tseg2_abr)
                if data_bitrate:
                    self.canFdConf.dataBitRate = int(data_bitrate)
                else:
                    self.canFdConf.dataBitRate = self.canFdConf.arbitrationBitRate
                self.canFdConf.sjwDbr = int(sjw_dbr)
                self.canFdConf.tseg1Dbr = int(tseg1_dbr)
                self.canFdConf.tseg2Dbr = int(tseg2_dbr)

                self.xldriver.xlCanFdSetConfiguration(
                    self.port_handle, self.mask, self.canFdConf
                )
                LOG.info(
                    "SetFdConfig.: ABaudr.=%u, DBaudr.=%u",
                    self.canFdConf.arbitrationBitRate,
                    self.canFdConf.dataBitRate,
                )
                LOG.info(
                    "SetFdConfig.: sjwAbr=%u, tseg1Abr=%u, tseg2Abr=%u",
                    self.canFdConf.sjwAbr,
                    self.canFdConf.tseg1Abr,
                    self.canFdConf.tseg2Abr,
                )
                LOG.info(
                    "SetFdConfig.: sjwDbr=%u, tseg1Dbr=%u, tseg2Dbr=%u",
                    self.canFdConf.sjwDbr,
                    self.canFdConf.tseg1Dbr,
                    self.canFdConf.tseg2Dbr,
                )
            else:
                if bitrate:
                    self.xldriver.xlCanSetChannelBitrate(
                        self.port_handle, permission_mask, bitrate
                    )
                    LOG.info("SetChannelBitrate: baudr.=%u", bitrate)
        else:
            LOG.info("No init access!")

        # Enable/disable TX receipts
        tx_receipts = 1 if receive_own_messages else 0
        self.xldriver.xlCanSetChannelMode(self.port_handle, self.mask, tx_receipts, 0)

        if HAS_EVENTS:
            self.event_handle = xlclass.XLhandle()
            self.xldriver.xlSetNotification(self.port_handle, self.event_handle, 1)
        else:
            LOG.info("Install pywin32 to avoid polling")

        try:
            self.xldriver.xlActivateChannel(
                self.port_handle, self.mask, xldefine.XL_BusTypes.XL_BUS_TYPE_CAN, 0
            )
        except VectorOperationError as error:
            self.shutdown()
            raise VectorInitializationError.from_generic(error) from None

        # Calculate time offset for absolute timestamps
        offset = xlclass.XLuint64()
        try:
            if time.get_clock_info("time").resolution > 1e-5:
                ts, perfcounter = time_perfcounter_correlation()
                try:
                    self.xldriver.xlGetSyncTime(self.port_handle, offset)
                except VectorInitializationError:
                    self.xldriver.xlGetChannelTime(self.port_handle, self.mask, offset)
                current_perfcounter = time.perf_counter()
                now = ts + (current_perfcounter - perfcounter)
                self._time_offset = now - offset.value * 1e-9
            else:
                try:
                    self.xldriver.xlGetSyncTime(self.port_handle, offset)
                except VectorInitializationError:
                    self.xldriver.xlGetChannelTime(self.port_handle, self.mask, offset)
                self._time_offset = time.time() - offset.value * 1e-9

        except VectorInitializationError:
            self._time_offset = 0.0

        self._is_filtered = False
        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

    def _apply_filters(self, filters: Optional[CanFilters]) -> None:
        if filters:
            # Only up to one filter per ID type allowed
            if len(filters) == 1 or (
                len(filters) == 2
                and filters[0].get("extended") != filters[1].get("extended")
            ):
                try:
                    for can_filter in filters:
                        self.xldriver.xlCanSetChannelAcceptance(
                            self.port_handle,
                            self.mask,
                            can_filter["can_id"],
                            can_filter["can_mask"],
                            xldefine.XL_AcceptanceFilter.XL_CAN_EXT
                            if can_filter.get("extended")
                            else xldefine.XL_AcceptanceFilter.XL_CAN_STD,
                        )
                except VectorOperationError as exception:
                    LOG.warning("Could not set filters: %s", exception)
                    # go to fallback
                else:
                    self._is_filtered = True
                    return
            else:
                LOG.warning("Only up to one filter per extended or standard ID allowed")
                # go to fallback

        # fallback: reset filters
        self._is_filtered = False
        try:
            self.xldriver.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                xldefine.XL_AcceptanceFilter.XL_CAN_EXT,
            )
            self.xldriver.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                xldefine.XL_AcceptanceFilter.XL_CAN_STD,
            )
        except VectorOperationError as exc:
            LOG.warning("Could not reset filters: %s", exc)

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:
        end_time = time.time() + timeout if timeout is not None else None

        while True:
            try:
                if self.fd:
                    msg = self._recv_canfd()
                else:
                    msg = self._recv_can()

            except VectorOperationError as exception:
                if exception.error_code != xldefine.XL_Status.XL_ERR_QUEUE_IS_EMPTY:
                    raise
            else:
                if msg:
                    return msg, self._is_filtered

            # if no message was received, wait or return on timeout
            if end_time is not None and time.time() > end_time:
                return None, self._is_filtered

            if HAS_EVENTS:
                # Wait for receive event to occur
                if end_time is None:
                    time_left_ms = INFINITE
                else:
                    time_left = end_time - time.time()
                    time_left_ms = max(0, int(time_left * 1000))
                WaitForSingleObject(self.event_handle.value, time_left_ms)  # type: ignore
            else:
                # Wait a short time until we try again
                time.sleep(self.poll_interval)

    def _recv_canfd(self) -> Optional[Message]:
        xl_can_rx_event = xlclass.XLcanRxEvent()
        self.xldriver.xlCanReceive(self.port_handle, xl_can_rx_event)

        if xl_can_rx_event.tag == xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_RX_OK:
            is_rx = True
            data_struct = xl_can_rx_event.tagData.canRxOkMsg
        elif xl_can_rx_event.tag == xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_TX_OK:
            is_rx = False
            data_struct = xl_can_rx_event.tagData.canTxOkMsg
        else:
            self.handle_canfd_event(xl_can_rx_event)
            return None

        msg_id = data_struct.canId
        dlc = dlc2len(data_struct.dlc)
        flags = data_struct.msgFlags
        timestamp = xl_can_rx_event.timeStamp * 1e-9
        channel = self.index_to_channel.get(xl_can_rx_event.chanIndex)

        return Message(
            timestamp=timestamp + self._time_offset,
            arbitration_id=msg_id & 0x1FFFFFFF,
            is_extended_id=bool(
                msg_id & xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID
            ),
            is_remote_frame=bool(
                flags & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_RTR
            ),
            is_error_frame=bool(
                flags & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EF
            ),
            is_fd=bool(flags & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EDL),
            bitrate_switch=bool(
                flags & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_BRS
            ),
            error_state_indicator=bool(
                flags & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_ESI
            ),
            is_rx=is_rx,
            channel=channel,
            dlc=dlc,
            data=data_struct.data[:dlc],
        )

    def _recv_can(self) -> Optional[Message]:
        xl_event = xlclass.XLevent()
        event_count = ctypes.c_uint(1)
        self.xldriver.xlReceive(self.port_handle, event_count, xl_event)

        if xl_event.tag != xldefine.XL_EventTags.XL_RECEIVE_MSG:
            self.handle_can_event(xl_event)
            return None

        msg_id = xl_event.tagData.msg.id
        dlc = xl_event.tagData.msg.dlc
        flags = xl_event.tagData.msg.flags
        timestamp = xl_event.timeStamp * 1e-9
        channel = self.index_to_channel.get(xl_event.chanIndex)

        return Message(
            timestamp=timestamp + self._time_offset,
            arbitration_id=msg_id & 0x1FFFFFFF,
            is_extended_id=bool(
                msg_id & xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID
            ),
            is_remote_frame=bool(
                flags & xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME
            ),
            is_error_frame=bool(
                flags & xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_ERROR_FRAME
            ),
            is_rx=not bool(
                flags & xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_TX_COMPLETED
            ),
            is_fd=False,
            dlc=dlc,
            data=xl_event.tagData.msg.data[:dlc],
            channel=channel,
        )

    def handle_can_event(self, event: xlclass.XLevent) -> None:
        """Handle non-message CAN events.

        Method is called by :meth:`~can.interfaces.vector.VectorBus._recv_internal`
        when `event.tag` is not `XL_RECEIVE_MSG`. Subclasses can implement this method.

        :param event: XLevent that could have a `XL_CHIP_STATE`, `XL_TIMER` or `XL_SYNC_PULSE` tag.
        """

    def handle_canfd_event(self, event: xlclass.XLcanRxEvent) -> None:
        """Handle non-message CAN FD events.

        Method is called by :meth:`~can.interfaces.vector.VectorBus._recv_internal`
        when `event.tag` is not `XL_CAN_EV_TAG_RX_OK` or `XL_CAN_EV_TAG_TX_OK`.
        Subclasses can implement this method.

        :param event: `XLcanRxEvent` that could have a `XL_CAN_EV_TAG_RX_ERROR`,
            `XL_CAN_EV_TAG_TX_ERROR`, `XL_TIMER` or `XL_CAN_EV_TAG_CHIP_STATE` tag.
        """

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        self._send_sequence([msg])

    def _send_sequence(self, msgs: Sequence[Message]) -> int:
        """Send messages and return number of successful transmissions."""
        if self.fd:
            return self._send_can_fd_msg_sequence(msgs)
        else:
            return self._send_can_msg_sequence(msgs)

    def _get_tx_channel_mask(self, msgs: Sequence[Message]) -> int:
        if len(msgs) == 1:
            return self.channel_masks.get(msgs[0].channel, self.mask)
        else:
            return self.mask

    def _send_can_msg_sequence(self, msgs: Sequence[Message]) -> int:
        """Send CAN messages and return number of successful transmissions."""
        mask = self._get_tx_channel_mask(msgs)
        message_count = ctypes.c_uint(len(msgs))

        xl_event_array = (xlclass.XLevent * message_count.value)(
            *map(self._build_xl_event, msgs)
        )

        self.xldriver.xlCanTransmit(
            self.port_handle, mask, message_count, xl_event_array
        )
        return message_count.value

    @staticmethod
    def _build_xl_event(msg: Message) -> xlclass.XLevent:
        msg_id = msg.arbitration_id
        if msg.is_extended_id:
            msg_id |= xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID

        flags = 0
        if msg.is_remote_frame:
            flags |= xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME

        xl_event = xlclass.XLevent()
        xl_event.tag = xldefine.XL_EventTags.XL_TRANSMIT_MSG
        xl_event.tagData.msg.id = msg_id
        xl_event.tagData.msg.dlc = msg.dlc
        xl_event.tagData.msg.flags = flags
        xl_event.tagData.msg.data = tuple(msg.data)

        return xl_event

    def _send_can_fd_msg_sequence(self, msgs: Sequence[Message]) -> int:
        """Send CAN FD messages and return number of successful transmissions."""
        mask = self._get_tx_channel_mask(msgs)
        message_count = len(msgs)

        xl_can_tx_event_array = (xlclass.XLcanTxEvent * message_count)(
            *map(self._build_xl_can_tx_event, msgs)
        )

        msg_count_sent = ctypes.c_uint(0)
        self.xldriver.xlCanTransmitEx(
            self.port_handle, mask, message_count, msg_count_sent, xl_can_tx_event_array
        )
        return msg_count_sent.value

    @staticmethod
    def _build_xl_can_tx_event(msg: Message) -> xlclass.XLcanTxEvent:
        msg_id = msg.arbitration_id
        if msg.is_extended_id:
            msg_id |= xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID

        flags = 0
        if msg.is_fd:
            flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_EDL
        if msg.bitrate_switch:
            flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_BRS
        if msg.is_remote_frame:
            flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_RTR

        xl_can_tx_event = xlclass.XLcanTxEvent()
        xl_can_tx_event.tag = xldefine.XL_CANFD_TX_EventTags.XL_CAN_EV_TAG_TX_MSG
        xl_can_tx_event.transId = 0xFFFF

        xl_can_tx_event.tagData.canMsg.canId = msg_id
        xl_can_tx_event.tagData.canMsg.msgFlags = flags
        xl_can_tx_event.tagData.canMsg.dlc = len2dlc(msg.dlc)
        xl_can_tx_event.tagData.canMsg.data = tuple(msg.data)

        return xl_can_tx_event

    def flush_tx_buffer(self) -> None:
        self.xldriver.xlCanFlushTransmitQueue(self.port_handle, self.mask)

    def shutdown(self) -> None:
        super().shutdown()
        self.xldriver.xlDeactivateChannel(self.port_handle, self.mask)
        self.xldriver.xlClosePort(self.port_handle)
        self.xldriver.xlCloseDriver()

    def reset(self) -> None:
        self.xldriver.xlDeactivateChannel(self.port_handle, self.mask)
        self.xldriver.xlActivateChannel(
            self.port_handle, self.mask, xldefine.XL_BusTypes.XL_BUS_TYPE_CAN, 0
        )

    @staticmethod
    def _detect_available_configs() -> List[AutoDetectedConfig]:
        configs = []
        channel_configs = get_channel_configs()
        LOG.info("Found %d channels", len(channel_configs))
        for channel_config in channel_configs:
            if (
                not channel_config.channelBusCapabilities
                & xldefine.XL_BusCapabilities.XL_BUS_ACTIVE_CAP_CAN
            ):
                continue
            LOG.info(
                "Channel index %d: %s", channel_config.channelIndex, channel_config.name
            )
            configs.append(
                {
                    # data for use in VectorBus.__init__():
                    "interface": "vector",
                    "channel": channel_config.hwChannel,
                    "serial": channel_config.serialNumber,
                    # data for use in VectorBus.set_application_config():
                    "hw_type": channel_config.hwType,
                    "hw_index": channel_config.hwIndex,
                    "hw_channel": channel_config.hwChannel,
                    # additional information:
                    "supports_fd": bool(
                        channel_config.channelCapabilities
                        & xldefine.XL_ChannelCapabilities.XL_CHANNEL_FLAG_CANFD_ISO_SUPPORT
                    ),
                    "vector_channel_config": channel_config,
                }
            )
        return configs  # type: ignore

    @staticmethod
    def popup_vector_hw_configuration(wait_for_finish: int = 0) -> None:
        """Open vector hardware configuration window.

        :param wait_for_finish:
            Time to wait for user input in milliseconds.
        """
        if xldriver is None:
            raise CanInterfaceNotImplementedError("The Vector API has not been loaded")

        xldriver.xlPopupHwConfig(ctypes.c_char_p(), ctypes.c_uint(wait_for_finish))

    @staticmethod
    def get_application_config(
        app_name: str, app_channel: int
    ) -> Tuple[xldefine.XL_HardwareType, int, int]:
        """Retrieve information for an application in Vector Hardware Configuration.

        :param app_name:
            The name of the application.
        :param app_channel:
            The channel of the application.
        :return:
            Returns a tuple of the hardware type, the hardware index and the
            hardware channel.

        :raises can.interfaces.vector.VectorInitializationError:
            If the application name does not exist in the Vector hardware configuration.
        """
        if xldriver is None:
            raise CanInterfaceNotImplementedError("The Vector API has not been loaded")

        hw_type = ctypes.c_uint()
        hw_index = ctypes.c_uint()
        hw_channel = ctypes.c_uint()
        _app_channel = ctypes.c_uint(app_channel)

        xldriver.xlGetApplConfig(
            app_name.encode(),
            _app_channel,
            hw_type,
            hw_index,
            hw_channel,
            xldefine.XL_BusTypes.XL_BUS_TYPE_CAN,
        )
        return xldefine.XL_HardwareType(hw_type.value), hw_index.value, hw_channel.value

    @staticmethod
    def set_application_config(
        app_name: str,
        app_channel: int,
        hw_type: xldefine.XL_HardwareType,
        hw_index: int,
        hw_channel: int,
        **kwargs: Any,
    ) -> None:
        """Modify the application settings in Vector Hardware Configuration.

        This method can also be used with a channel config dictionary::

            import can
            from can.interfaces.vector import VectorBus

            configs = can.detect_available_configs(interfaces=['vector'])
            cfg = configs[0]
            VectorBus.set_application_config(app_name="MyApplication", app_channel=0, **cfg)

        :param app_name:
            The name of the application. Creates a new application if it does
            not exist yet.
        :param app_channel:
            The channel of the application.
        :param hw_type:
            The hardware type of the interface.
            E.g XL_HardwareType.XL_HWTYPE_VIRTUAL
        :param hw_index:
            The index of the interface if multiple interface with the same
            hardware type are present.
        :param hw_channel:
            The channel index of the interface.

        :raises can.interfaces.vector.VectorInitializationError:
            If the application name does not exist in the Vector hardware configuration.
        """
        if xldriver is None:
            raise CanInterfaceNotImplementedError("The Vector API has not been loaded")

        xldriver.xlSetApplConfig(
            app_name.encode(),
            app_channel,
            hw_type,
            hw_index,
            hw_channel,
            xldefine.XL_BusTypes.XL_BUS_TYPE_CAN,
        )

    def set_timer_rate(self, timer_rate_ms: int) -> None:
        """Set the cyclic event rate of the port.

        Once set, the port will generate a cyclic event with the tag XL_EventTags.XL_TIMER.
        This timer can be used to keep an application alive. See XL Driver Library Description
        for more information

        :param timer_rate_ms:
            The timer rate in ms. The minimal timer rate is 1ms, a value of 0 deactivates
            the timer events.
        """
        timer_rate_10us = timer_rate_ms * 100
        self.xldriver.xlSetTimerRate(self.port_handle, timer_rate_10us)


class VectorChannelConfig(NamedTuple):
    name: str
    hwType: xldefine.XL_HardwareType
    hwIndex: int
    hwChannel: int
    channelIndex: int
    channelMask: int
    channelCapabilities: xldefine.XL_ChannelCapabilities
    channelBusCapabilities: xldefine.XL_BusCapabilities
    isOnBus: bool
    connectedBusType: xldefine.XL_BusTypes
    serialNumber: int
    articleNumber: int
    transceiverName: str


def get_channel_configs() -> List[VectorChannelConfig]:
    if xldriver is None:
        return []
    driver_config = xlclass.XLdriverConfig()
    try:
        xldriver.xlOpenDriver()
        xldriver.xlGetDriverConfig(driver_config)
        xldriver.xlCloseDriver()
    except VectorError:
        pass

    channel_list: List[VectorChannelConfig] = []
    for i in range(driver_config.channelCount):
        xlcc: xlclass.XLchannelConfig = driver_config.channel[i]
        vcc = VectorChannelConfig(
            name=xlcc.name.decode(),
            hwType=xldefine.XL_HardwareType(xlcc.hwType),
            hwIndex=xlcc.hwIndex,
            hwChannel=xlcc.hwChannel,
            channelIndex=xlcc.channelIndex,
            channelMask=xlcc.channelMask,
            channelCapabilities=xldefine.XL_ChannelCapabilities(
                xlcc.channelCapabilities
            ),
            channelBusCapabilities=xldefine.XL_BusCapabilities(
                xlcc.channelBusCapabilities
            ),
            isOnBus=bool(xlcc.isOnBus),
            connectedBusType=xldefine.XL_BusTypes(xlcc.connectedBusType),
            serialNumber=xlcc.serialNumber,
            articleNumber=xlcc.articleNumber,
            transceiverName=xlcc.transceiverName.decode(),
        )
        channel_list.append(vcc)
    return channel_list

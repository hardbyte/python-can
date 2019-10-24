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
from typing import Any, Dict, List, Optional, Union

try:
    # Try builtin Python 3 Windows API
    from _winapi import WaitForSingleObject, INFINITE

    HAS_EVENTS = True
except ImportError:
    try:
        # Try pywin32 package
        from win32event import WaitForSingleObject, INFINITE

        HAS_EVENTS = True
    except ImportError:
        # Use polling instead
        HAS_EVENTS = False

# Import Modules
# ==============
from can import BusABC, Message
from can.util import len2dlc, dlc2len
from .exceptions import VectorError
from can.bit_timing import BitTiming

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Import Vector API module
# ========================
from . import xldefine, xlclass

# Import safely Vector API module for Travis tests
xldriver = None
try:
    from . import xldriver
except Exception as exc:
    LOG.warning("Could not import vxlapi: %s", exc)


class VectorBus(BusABC):
    """The CAN Bus implemented for the Vector interface."""

    def __init__(
        self,
        channel: Union[int, List[int]],
        can_filters: Optional[List[Dict[str, int]]] = None,
        poll_interval: float = 0.01,
        receive_own_messages: bool = False,
        bitrate: Optional[int] = None,
        timing: Optional[BitTiming] = None,
        data_timing: Optional[BitTiming] = None,
        rx_queue_size: int = 2 ** 14,
        app_name: str = "CANalyzer",
        serial: Optional[int] = None,
        fd: bool = False,
        data_bitrate: Optional[int] = None,
        sjwAbr: int = 2,
        tseg1Abr: int = 6,
        tseg2Abr: int = 3,
        sjwDbr: int = 2,
        tseg1Dbr: int = 6,
        tseg2Dbr: int = 3,
        **kwargs,
    ):
        """
        :param list channel:
            The channel indexes to create this bus with.
            Can also be a single integer or a comma separated string.
        :param float poll_interval:
            Poll interval in seconds.
        :param int bitrate:
            Bitrate in bits/s.
        :param can.BitTiming timing:
            Bit timing configuration.
            For CAN-FD this also applies to arbitration/nominal phase if no data_timing is provided.
        :param can.BitTiming data_timing:
            Bit timing configuration for CAN FD data phase.
        :param int rx_queue_size:
            Number of messages in receive queue (power of 2).
            CAN: range 16…32768
            CAN-FD: range 8192…524288
        :param str app_name:
            Name of application in Hardware Config.
            If set to None, the channel should be a global channel index.
        :param int serial:
            Serial number of the hardware to be used.
            If set, the channel parameter refers to the channels ONLY on the specified hardware.
            If set, the app_name is unused.
        :param bool fd:
            If CAN-FD frames should be supported.
        :param int data_bitrate:
            Which bitrate to use for data phase in CAN FD.
            Defaults to arbitration bitrate.
        """
        if os.name != "nt" and not kwargs.get("_testing", False):
            raise OSError(
                f'The Vector interface is only supported on Windows, but you are running "{os.name}"'
            )

        if xldriver is None:
            raise ImportError("The Vector API has not been loaded")

        self.poll_interval = poll_interval
        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(",")]
        self._app_name = app_name.encode() if app_name is not None else ""
        self.channel_info = "Application %s: %s" % (
            app_name,
            ", ".join("CAN %d" % (ch + 1) for ch in self.channels),
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
                raise Exception(
                    "None of the configured channels could be found on the specified hardware."
                )

        xldriver.xlOpenDriver()
        self.port_handle = xlclass.XLportHandle(xldefine.XL_INVALID_PORTHANDLE)
        self.mask = 0
        self.fd = fd
        # Get channels masks
        self.channel_masks = {}
        self.index_to_channel = {}

        for channel in self.channels:
            if app_name:
                # Get global channel index from application channel
                hw_type = ctypes.c_uint(0)
                hw_index = ctypes.c_uint(0)
                hw_channel = ctypes.c_uint(0)
                xldriver.xlGetApplConfig(
                    self._app_name,
                    channel,
                    hw_type,
                    hw_index,
                    hw_channel,
                    xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value,
                )
                LOG.debug(f"Channel index {channel} found")
                idx = xldriver.xlGetChannelIndex(
                    hw_type.value, hw_index.value, hw_channel.value
                )
                if idx < 0:
                    # Undocumented behavior! See issue #353.
                    # If hardware is unavailable, this function returns -1.
                    # Raise an exception as if the driver
                    # would have signalled XL_ERR_HW_NOT_PRESENT.
                    raise VectorError(
                        xldefine.XL_Status.XL_ERR_HW_NOT_PRESENT.value,
                        "XL_ERR_HW_NOT_PRESENT",
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
        if bitrate or fd or timing:
            permission_mask.value = self.mask
        if fd:
            xldriver.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                permission_mask,
                rx_queue_size,
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION_V4.value,
                xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value,
            )
        else:
            xldriver.xlOpenPort(
                self.port_handle,
                self._app_name,
                self.mask,
                permission_mask,
                rx_queue_size,
                xldefine.XL_InterfaceVersion.XL_INTERFACE_VERSION.value,
                xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value,
            )
        LOG.debug(
            f"xlOpenPort: "
            f"PortHandle={self.port_handle.value}, "
            f"PermissionMask={permission_mask.value}"
        )

        # If application has init access, set CAN settings
        if permission_mask.value == self.mask:
            if fd:
                self.canFdConf = self._get_canfdconf(
                    timing,
                    data_timing,
                    bitrate,
                    sjwAbr,
                    tseg1Abr,
                    tseg2Abr,
                    data_bitrate,
                    sjwDbr,
                    tseg1Dbr,
                    tseg2Dbr,
                )

                xldriver.xlCanFdSetConfiguration(
                    self.port_handle, self.mask, self.canFdConf
                )
                LOG.info(
                    f"xlCanFdSetConfiguration: "
                    f"arbitrationBitRate={self.canFdConf.arbitrationBitRate}, "
                    f"sjwAbr={self.canFdConf.sjwAbr}, "
                    f"tseg1Abr={self.canFdConf.tseg1Abr}, "
                    f"tseg2Abr={self.canFdConf.tseg2Abr}, "
                    f"dataBitRate={self.canFdConf.dataBitRate}, "
                    f"sjwDbr={self.canFdConf.sjwDbr}, "
                    f"tseg1Dbr={self.canFdConf.tseg1Dbr}, "
                    f"tseg2Dbr={self.canFdConf.tseg2Dbr}"
                )
            else:
                if timing:
                    self.chipParams = self._get_chipparams(timing)
                    xldriver.xlCanSetChannelParams(
                        self.port_handle, self.mask, self.chipParams
                    )
                    LOG.info(
                        f"xlCanSetChannelParams: "
                        f"bitRate={self.chipParams.bitRate}, "
                        f"sjwAbr={self.chipParams.sjw}, "
                        f"tseg1={self.chipParams.tseg1}, "
                        f"tseg2={self.chipParams.tseg2}, "
                        f"sam={self.chipParams.sam}"
                    )
                elif bitrate:
                    xldriver.xlCanSetChannelBitrate(
                        self.port_handle, permission_mask, bitrate
                    )
                    LOG.info(f"xlCanSetChannelBitrate: bitrate={bitrate}")
        else:
            LOG.info("No init access!")

        # Enable/disable TX receipts
        tx_receipts = 1 if receive_own_messages else 0
        xldriver.xlCanSetChannelMode(self.port_handle, self.mask, tx_receipts, 0)

        if HAS_EVENTS:
            self.event_handle = xlclass.XLhandle()
            xldriver.xlSetNotification(self.port_handle, self.event_handle, 1)
        else:
            LOG.info("Install pywin32 to avoid polling")

        try:
            xldriver.xlActivateChannel(
                self.port_handle,
                self.mask,
                xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value,
                0,
            )
        except VectorError:
            self.shutdown()
            raise

        # Calculate time offset for absolute timestamps
        offset = xlclass.XLuint64()
        xldriver.xlGetSyncTime(self.port_handle, offset)
        self._time_offset = time.time() - offset.value * 1e-9

        self._is_filtered = False
        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

    @staticmethod
    def _get_canfdconf(
        timing: Optional[BitTiming] = None,
        data_timing: Optional[BitTiming] = None,
        bitrate: Optional[int] = None,
        sjwAbr: Optional[int] = None,
        tseg1Abr: Optional[int] = None,
        tseg2Abr: Optional[int] = None,
        data_bitrate: Optional[int] = None,
        sjwDbr: Optional[int] = None,
        tseg1Dbr: Optional[int] = None,
        tseg2Dbr: Optional[int] = None,
    ) -> xlclass.XLcanFdConf:
        canFdConf = xlclass.XLcanFdConf()
        if timing:
            canFdConf.arbitrationBitRate = ctypes.c_uint(timing.bitrate)
            canFdConf.sjwAbr = ctypes.c_uint(timing.sjw)
            canFdConf.tseg1Abr = ctypes.c_uint(timing.tseg1)
            canFdConf.tseg2Abr = ctypes.c_uint(timing.tseg2)
            if data_timing:
                canFdConf.dataBitRate = ctypes.c_uint(data_timing.bitrate)
                canFdConf.sjwDbr = ctypes.c_uint(data_timing.sjw)
                canFdConf.tseg1Dbr = ctypes.c_uint(data_timing.tseg1)
                canFdConf.tseg2Dbr = ctypes.c_uint(data_timing.tseg2)
            else:
                canFdConf.dataBitRate = ctypes.c_uint(timing.bitrate)
                canFdConf.sjwDbr = ctypes.c_uint(timing.sjw)
                canFdConf.tseg1Dbr = ctypes.c_uint(timing.tseg1)
                canFdConf.tseg2Dbr = ctypes.c_uint(timing.tseg2)
        else:
            if bitrate:
                canFdConf.arbitrationBitRate = ctypes.c_uint(bitrate)
            else:
                canFdConf.arbitrationBitRate = ctypes.c_uint(500000)
            canFdConf.sjwAbr = ctypes.c_uint(sjwAbr)
            canFdConf.tseg1Abr = ctypes.c_uint(tseg1Abr)
            canFdConf.tseg2Abr = ctypes.c_uint(tseg2Abr)
            if data_bitrate:
                canFdConf.dataBitRate = ctypes.c_uint(data_bitrate)
            else:
                canFdConf.dataBitRate = canFdConf.arbitrationBitRate
            canFdConf.sjwDbr = ctypes.c_uint(sjwDbr)
            canFdConf.tseg1Dbr = ctypes.c_uint(tseg1Dbr)
            canFdConf.tseg2Dbr = ctypes.c_uint(tseg2Dbr)

        return canFdConf

    @staticmethod
    def _get_chipparams(timing: BitTiming) -> xlclass.XLchipParams:
        chipParams = xlclass.XLchipParams()
        chipParams.bitRate = ctypes.c_ulong(timing.bitrate)
        chipParams.sjw = ctypes.c_ubyte(timing.sjw)
        chipParams.tseg1 = ctypes.c_ubyte(timing.tseg1)
        chipParams.tseg2 = ctypes.c_ubyte(timing.tseg2)
        chipParams.sam = ctypes.c_ubyte(timing.nof_samples)
        return chipParams

    def _apply_filters(self, filters: List[Dict[str, int]]):
        if filters:
            # Only up to one filter per ID type allowed
            if len(filters) == 1 or (
                len(filters) == 2
                and filters[0].get("extended") != filters[1].get("extended")
            ):
                try:
                    for can_filter in filters:
                        xldriver.xlCanSetChannelAcceptance(
                            self.port_handle,
                            self.mask,
                            can_filter["can_id"],
                            can_filter["can_mask"],
                            xldefine.XL_AcceptanceFilter.XL_CAN_EXT.value
                            if can_filter.get("extended")
                            else xldefine.XL_AcceptanceFilter.XL_CAN_STD.value,
                        )
                except VectorError as exc:
                    LOG.warning("Could not set filters: %s", exc)
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
            xldriver.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                xldefine.XL_AcceptanceFilter.XL_CAN_EXT.value,
            )
            xldriver.xlCanSetChannelAcceptance(
                self.port_handle,
                self.mask,
                0x0,
                0x0,
                xldefine.XL_AcceptanceFilter.XL_CAN_STD.value,
            )
        except VectorError as exc:
            LOG.warning("Could not reset filters: %s", exc)

    def _recv_internal(self, timeout):
        end_time = time.time() + timeout if timeout is not None else None

        if self.fd:
            event = xlclass.XLcanRxEvent()
        else:
            event = xlclass.XLevent()
            event_count = ctypes.c_uint()

        while True:
            if self.fd:
                try:
                    xldriver.xlCanReceive(self.port_handle, event)
                except VectorError as exc:
                    if exc.error_code != xldefine.XL_Status.XL_ERR_QUEUE_IS_EMPTY.value:
                        raise
                else:
                    if (
                        event.tag
                        == xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_RX_OK.value
                        or event.tag
                        == xldefine.XL_CANFD_RX_EventTags.XL_CAN_EV_TAG_TX_OK.value
                    ):
                        msg_id = event.tagData.canRxOkMsg.canId
                        dlc = dlc2len(event.tagData.canRxOkMsg.dlc)
                        flags = event.tagData.canRxOkMsg.msgFlags
                        timestamp = event.timeStamp * 1e-9
                        channel = self.index_to_channel.get(event.chanIndex)
                        msg = Message(
                            timestamp=timestamp + self._time_offset,
                            arbitration_id=msg_id & 0x1FFFFFFF,
                            is_extended_id=bool(
                                msg_id
                                & xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value
                            ),
                            is_remote_frame=bool(
                                flags
                                & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_RTR.value
                            ),
                            is_error_frame=bool(
                                flags
                                & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EF.value
                            ),
                            is_fd=bool(
                                flags
                                & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_EDL.value
                            ),
                            error_state_indicator=bool(
                                flags
                                & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_ESI.value
                            ),
                            bitrate_switch=bool(
                                flags
                                & xldefine.XL_CANFD_RX_MessageFlags.XL_CAN_RXMSG_FLAG_BRS.value
                            ),
                            dlc=dlc,
                            data=event.tagData.canRxOkMsg.data[:dlc],
                            channel=channel,
                        )
                        return msg, self._is_filtered
            else:
                event_count.value = 1
                try:
                    xldriver.xlReceive(self.port_handle, event_count, event)
                except VectorError as exc:
                    if exc.error_code != xldefine.XL_Status.XL_ERR_QUEUE_IS_EMPTY.value:
                        raise
                else:
                    if event.tag == xldefine.XL_EventTags.XL_RECEIVE_MSG.value:
                        msg_id = event.tagData.msg.id
                        dlc = event.tagData.msg.dlc
                        flags = event.tagData.msg.flags
                        timestamp = event.timeStamp * 1e-9
                        channel = self.index_to_channel.get(event.chanIndex)
                        msg = Message(
                            timestamp=timestamp + self._time_offset,
                            arbitration_id=msg_id & 0x1FFFFFFF,
                            is_extended_id=bool(
                                msg_id
                                & xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value
                            ),
                            is_remote_frame=bool(
                                flags
                                & xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME.value
                            ),
                            is_error_frame=bool(
                                flags
                                & xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_ERROR_FRAME.value
                            ),
                            is_fd=False,
                            dlc=dlc,
                            data=event.tagData.msg.data[:dlc],
                            channel=channel,
                        )
                        return msg, self._is_filtered

            if end_time is not None and time.time() > end_time:
                return None, self._is_filtered

            if HAS_EVENTS:
                # Wait for receive event to occur
                if timeout is None:
                    time_left_ms = INFINITE
                else:
                    time_left = end_time - time.time()
                    time_left_ms = max(0, int(time_left * 1000))
                WaitForSingleObject(self.event_handle.value, time_left_ms)
            else:
                # Wait a short time until we try again
                time.sleep(self.poll_interval)

    def send(self, msg, timeout=None):
        msg_id = msg.arbitration_id

        if msg.is_extended_id:
            msg_id |= xldefine.XL_MessageFlagsExtended.XL_CAN_EXT_MSG_ID.value

        flags = 0

        # If channel has been specified, try to send only to that one.
        # Otherwise send to all channels
        mask = self.channel_masks.get(msg.channel, self.mask)

        if self.fd:
            if msg.is_fd:
                flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_EDL.value
            if msg.bitrate_switch:
                flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_BRS.value
            if msg.is_remote_frame:
                flags |= xldefine.XL_CANFD_TX_MessageFlags.XL_CAN_TXMSG_FLAG_RTR.value

            message_count = 1
            MsgCntSent = ctypes.c_uint(1)

            XLcanTxEvent = xlclass.XLcanTxEvent()
            XLcanTxEvent.tag = xldefine.XL_CANFD_TX_EventTags.XL_CAN_EV_TAG_TX_MSG.value
            XLcanTxEvent.transId = 0xFFFF

            XLcanTxEvent.tagData.canMsg.canId = msg_id
            XLcanTxEvent.tagData.canMsg.msgFlags = flags
            XLcanTxEvent.tagData.canMsg.dlc = len2dlc(msg.dlc)
            for idx, value in enumerate(msg.data):
                XLcanTxEvent.tagData.canMsg.data[idx] = value
            xldriver.xlCanTransmitEx(
                self.port_handle, mask, message_count, MsgCntSent, XLcanTxEvent
            )

        else:
            if msg.is_remote_frame:
                flags |= xldefine.XL_MessageFlags.XL_CAN_MSG_FLAG_REMOTE_FRAME.value

            message_count = ctypes.c_uint(1)

            xl_event = xlclass.XLevent()
            xl_event.tag = xldefine.XL_EventTags.XL_TRANSMIT_MSG.value

            xl_event.tagData.msg.id = msg_id
            xl_event.tagData.msg.dlc = msg.dlc
            xl_event.tagData.msg.flags = flags
            for idx, value in enumerate(msg.data):
                xl_event.tagData.msg.data[idx] = value
            xldriver.xlCanTransmit(self.port_handle, mask, message_count, xl_event)

    def flush_tx_buffer(self):
        xldriver.xlCanFlushTransmitQueue(self.port_handle, self.mask)

    def shutdown(self):
        xldriver.xlDeactivateChannel(self.port_handle, self.mask)
        xldriver.xlClosePort(self.port_handle)
        xldriver.xlCloseDriver()

    def reset(self):
        xldriver.xlDeactivateChannel(self.port_handle, self.mask)
        xldriver.xlActivateChannel(
            self.port_handle, self.mask, xldefine.XL_BusTypes.XL_BUS_TYPE_CAN.value, 0
        )

    @staticmethod
    def _detect_available_configs() -> List[Dict[str, Any]]:
        configs = []
        channel_configs = get_channel_configs()
        LOG.info("Found %d channels", len(channel_configs))
        for channel_config in channel_configs:
            if (
                not channel_config.channelBusCapabilities
                & xldefine.XL_BusCapabilities.XL_BUS_ACTIVE_CAP_CAN.value
            ):
                continue
            LOG.info(
                "Channel index %d: %s",
                channel_config.channelIndex,
                channel_config.name.decode("ascii"),
            )
            configs.append(
                {
                    "interface": "vector",
                    "app_name": None,
                    "channel": channel_config.channelIndex,
                    "supports_fd": bool(
                        channel_config.channelBusCapabilities
                        & xldefine.XL_ChannelCapabilities.XL_CHANNEL_FLAG_CANFD_ISO_SUPPORT.value
                    ),
                }
            )
        return configs


def get_channel_configs():
    if xldriver is None:
        return []
    driver_config = xlclass.XLdriverConfig()
    try:
        xldriver.xlOpenDriver()
        xldriver.xlGetDriverConfig(driver_config)
        xldriver.xlCloseDriver()
    except Exception:
        pass
    return [driver_config.channel[i] for i in range(driver_config.channelCount)]

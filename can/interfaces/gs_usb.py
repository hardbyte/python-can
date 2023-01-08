from typing import Optional, Tuple

from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GsUsbFrame, GS_USB_NONE_ECHO_ID
from gs_usb.constants import CAN_ERR_FLAG, CAN_RTR_FLAG, CAN_EFF_FLAG, CAN_MAX_DLC
import can
import usb
import logging

from ..exceptions import CanInitializationError, CanOperationError


logger = logging.getLogger(__name__)


class GsUsbBus(can.BusABC):
    def __init__(
        self,
        channel,
        bitrate,
        index=None,
        bus=None,
        address=None,
        can_filters=None,
        **kwargs,
    ):
        """
        :param channel: usb device name
        :param index: device number if using automatic scan, starting from 0.
            If specified, bus/address shall not be provided.
        :param bus: number of the bus that the device is connected to
        :param address: address of the device on the bus it is connected to
        :param can_filters: not supported
        :param bitrate: CAN network bandwidth (bits/s)
        """
        if (index is not None) and ((bus or address) is not None):
            raise CanInitializationError(
                f"index and bus/address cannot be used simultaneously"
            )

        if index is not None:
            devs = GsUsb.scan()
            if len(devs) <= index:
                raise CanInitializationError(
                    f"Cannot find device {index}. Devices found: {len(devs)}"
                )
            gs_usb = devs[index]
        else:
            gs_usb = GsUsb.find(bus=bus, address=address)
            if not gs_usb:
                raise CanInitializationError(f"Cannot find device {channel}")

        self.gs_usb = gs_usb
        self.channel_info = channel

        self.gs_usb.set_bitrate(bitrate)
        self.gs_usb.start()

        super().__init__(channel=channel, can_filters=can_filters, **kwargs)

    def send(self, msg: can.Message, timeout: Optional[float] = None):
        """Transmit a message to the CAN bus.

        :param Message msg: A message object.
        :param timeout: timeout is not supported.
            The function won't return until message is sent or exception is raised.

        :raises CanOperationError:
            if the message could not be sent
        """
        can_id = msg.arbitration_id

        if msg.is_extended_id:
            can_id = can_id | CAN_EFF_FLAG

        if msg.is_remote_frame:
            can_id = can_id | CAN_RTR_FLAG

        if msg.is_error_frame:
            can_id = can_id | CAN_ERR_FLAG

        # Pad message data
        msg.data.extend([0x00] * (CAN_MAX_DLC - len(msg.data)))

        frame = GsUsbFrame()
        frame.can_id = can_id
        frame.can_dlc = msg.dlc
        frame.timestamp_us = int(msg.timestamp * 1000000)
        frame.data = list(msg.data)

        try:
            self.gs_usb.send(frame)
        except usb.core.USBError:
            raise CanOperationError("The message could not be sent")

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[can.Message], bool]:
        """
        Read a message from the bus and tell whether it was filtered.
        This methods may be called by :meth:`~can.BusABC.recv`
        to read a message multiple times if the filters set by
        :meth:`~can.BusABC.set_filters` do not match and the call has
        not yet timed out.

        Never raises an error/exception.

        :param float timeout: seconds to wait for a message,
                              see :meth:`~can.BusABC.send`
                              0 and None will be converted to minimum value 1ms.

        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False. In this interface it is always False
                since filtering is not available
        """
        frame = GsUsbFrame()

        # Do not set timeout as None or zero here to avoid blocking
        timeout_ms = round(timeout * 1000) if timeout else 1
        if not self.gs_usb.read(frame=frame, timeout_ms=timeout_ms):
            return None, False

        msg = can.Message(
            timestamp=frame.timestamp,
            arbitration_id=frame.arbitration_id,
            is_extended_id=frame.is_extended_id,
            is_remote_frame=frame.is_remote_frame,
            is_error_frame=frame.is_error_frame,
            channel=self.channel_info,
            dlc=frame.can_dlc,
            data=bytearray(frame.data)[0 : frame.can_dlc],
            is_rx=frame.echo_id == GS_USB_NONE_ECHO_ID,
        )

        return msg, False

    def shutdown(self):
        super().shutdown()
        self.gs_usb.stop()

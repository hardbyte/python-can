import can.interfaces.ixxat.canlib_vcinpl as vcinpl
import can.interfaces.ixxat.canlib_vcinpl2 as vcinpl2

from can import BusABC, Message
from typing import Optional


class IXXATBus(BusABC):
    """The CAN Bus implemented for the IXXAT interface.

    Based on the C implementation of IXXAT, two different dlls are provided by IXXAT, one to work with CAN,
    the other with CAN-FD.

    This class only delegates to related implementation (in calib_vcinpl or canlib_vcinpl2) class depending on fd user option.
    """

    def __init__(self, channel, can_filters=None, **kwargs):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param bool receive_own_messages:
            Enable self-reception of sent messages.

        :param int UniqueHardwareId:
            UniqueHardwareId to connect (optional, will use the first found if not supplied)

        : param bool fd:
        Default False, enables CAN-FD usage.

        :param int bitrate:
            Channel bitrate in bit/s

        :param int data_bitrate:
            Channel bitrate in bit/s (only in CAN-Fd if baudrate switch enabled).

        :param int extended:
            Default False, enables the capability to use extended IDs.

        """
        if kwargs.get("fd", False):
            self.bus = vcinpl2.IXXATBus(channel, can_filters=None, **kwargs)
        else:
            self.bus = vcinpl.IXXATBus(channel, can_filters=None, **kwargs)

    def flush_tx_buffer(self):
        """Flushes the transmit buffer on the IXXAT"""
        return self.bus.flush_tx_buffer()

    def _recv_internal(self, timeout):
        return self.bus._recv_internal(timeout)

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        return self.bus.send(msg, timeout)

    def _send_periodic_internal(self, msg, period, duration=None):
        return self.bus._send_periodic_internal(msg, period, duration)

    def shutdown(self):
        return self.bus.shutdown()

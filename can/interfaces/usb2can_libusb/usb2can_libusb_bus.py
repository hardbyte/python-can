"""
This interface requires LibUSB and `pyusb` to be installed on your system.
The interface will bind by default to the first device with VID  
"""

import logging
from ctypes import byref

from can import BusABC, Message, CanError, BitTiming
from .can_8dev_usb_device import *

# Set up logging
log = logging.getLogger("can.usb2can_libusb")

def message_convert_tx(msg):
    """convert message from PythonCAN Message to 8Devices frame"""
    return Can8DevTxFrame(can_id = msg.arbitration_id, dlc = msg.dlc, data = msg.data, is_ext = msg.is_extended_id, is_remote = msg.is_remote_frame)

def message_convert_rx(message_rx: Can8DevRxFrame):
    """convert message from 8Devices frame to PythonCAN Message"""

    if(message_rx.is_error):
        return Message(
            timestamp=message_rx.timestamp / 1000,
            is_error_frame=message_rx.is_error,
            data=message_rx.data
        )
    
    return Message(
        timestamp=message_rx.timestamp / 1000,
        is_remote_frame=message_rx.is_remote,
        is_extended_id=message_rx.ext_id,
        is_error_frame=message_rx.is_error,
        arbitration_id=message_rx.id,
        dlc=message_rx.dlc,
        data=message_rx.data[: message_rx.dlc],
    )


class Usb2CanLibUsbBus(BusABC):
    """Interface to an 8Devices USB2CAN Bus.

    This device should work on any platform with a working LibUSB and PyUSB. It was tested with a "Korlan USB2Can" but should work with the older module as well.

    Hardware filtering is not provided, if anyone knows how the 8Devices filtering command works, this would be valuable.

    Based on the in-tree Linux kernel SocketCAN driver for USB2CAN.

    :param str channel (optional):
        The device's serial number. If not provided, the first matching VID/DID will match (WARNING: 8Devices reuse a random ST VID/DID, so other devices may match!)

    :param int bitrate (optional):
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param int flags (optional):
        Flags to directly pass to open function of the usb2can abstraction layer.
    """

    def __init__(
        self,
        channel=None,
        *args,
        bitrate=500000,
        **kwargs
    ):

        self.can = Can8DevUSBDevice()

        # convert to kb/s and cap: max rate is 1000 kb/s
        baudrate = min(int(bitrate // 1000), 1000)

        self.channel_info = "USB2CAN LibUSB device {}".format(self.can.get_serial_number())

        connector = "{}; {}".format("USB2Can_LibUSB", baudrate)

        timing = BitTiming(tseg1=6, tseg2=1, sjw=1, bitrate = bitrate, f_clock = USB_8DEV_ABP_CLOCK)
        self.can.open(timing.tseg1, timing.tseg2, timing.sjw, timing.brp)

        super().__init__(
            channel=channel, bitrate=bitrate, *args, **kwargs
        )

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)
        if(timeout is not None):
            timeout *= 1000
        self.can.send(tx, timeout)

    def _recv_internal(self, timeout):
        if(timeout is not None):
            timeout *= 1000
        messagerx = self.can.recv(timeout)
        rx = None
        if(messagerx is not None):
            rx = message_convert_rx(messagerx)
        return rx, False

    def shutdown(self):
        """
        Shuts down connection to the device.
        """
        self.can.close()
"""
Enable basic can over a serial device.

E.g. over bluetooth with "/dev/rfcomm0"

"""

import logging

logger = logging.getLogger('can.serial')

try:
    import serial
except ImportError:
    logger.error("You won't be able to use the serial can backend without the serial module installed!")
    serial = None

from can.bus import BusABC
from can.message import Message


class SerialBus(BusABC):

    def __init__(self, channel, *args, **kwargs):
        """A serial interface to CAN.

        :param str channel:
            The serial device to open.
        """
        if channel == '':
            raise TypeError("Must specify a serial port.")
        else:
            self.channel_info = "Serial interface: " + channel

            # Note: Some serial port implementations don't care about the baud rate
            self.ser = serial.Serial(channel, baudrate=115200, timeout=0.1)
        super(SerialBus, self).__init__(*args, **kwargs)

    def _put_message(self, msg):
        raise NotImplementedError("This serial interface doesn't support transmit.")

    def _get_message(self, timeout=None):

        try:
            # ser.read can return an empty string ''
            # or raise a SerialException
            rx_byte = self.ser.read()
        except serial.SerialException:
            return None

        if len(rx_byte) and ord(rx_byte) == 0xAA:
            s = bytearray(self.ser.read(4))
            timestamp = s[0] + (s[1] << 8) + (s[2] << 16) + (s[3] << 24)
            dlc = ord(self.ser.read())

            s = bytearray(self.ser.read(4))
            arb_id = s[0] + (s[1] << 8) + (s[2] << 16) + (s[3] << 24)

            data = self.ser.read(dlc)

            rxd_byte = ord(self.ser.read())
            if rxd_byte == 0xBB:
                # received message data okay
                return Message(timestamp=timestamp, arbitration_id=arb_id, dlc=dlc, data=data)
            else:
                return None

        else:
            return None

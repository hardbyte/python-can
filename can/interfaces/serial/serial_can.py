"""
Enable basic can over a serial device.

E.g. over bluetooth with "/dev/rfcomm0" or with Arduino "/dev/ttyACM0"

"""
# TODO write documentation for serial specification
# TODO add class and function documentation
# TODO link to arduino example
# TODO normal and extended id

import logging

logger = logging.getLogger('can.serial')

try:
    import serial
except ImportError:
    logger.error("You won't be able to use the serial can backend without the "
                 "serial module installed!")
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
            bitrate = kwargs.get('bitrate', 115200)
            timeout = kwargs.get('timeout', 0.1)
            # Note: Some serial port implementations don't care about the baud rate
            self.ser = serial.Serial(channel, baudrate=bitrate, timeout=timeout)
        super(SerialBus, self).__init__(*args, **kwargs)

    def shutdown(self):
        self.ser.close()

    def send(self, msg, timeout=None):
        timestamp = msg.timestamp.to_bytes(4, byteorder='little')
        a_id = msg.arbitration_id.to_bytes(4, byteorder='little')
        dlc = msg.dlc.to_bytes(1, byteorder='little')
        byte_msg = bytes([0xAA]) + timestamp + dlc + a_id + msg.data + \
                   bytes([0xBB])
        self.ser.write(byte_msg)

    def recv(self, timeout=None):
        try:
            # ser.read can return an empty string ''
            # or raise a SerialException
            rx_byte = self.ser.read()
        except serial.SerialException:
            return None

        if len(rx_byte) and ord(rx_byte) == 0xAA:
            s = bytearray(self.ser.read(4))
            timestamp = int.from_bytes(s, byteorder='little', signed=False)
            dlc = ord(self.ser.read())

            s = bytearray(self.ser.read(4))
            arb_id = int.from_bytes(s, byteorder='little', signed=False)

            data = self.ser.read(dlc)

            rxd_byte = ord(self.ser.read())
            if rxd_byte == 0xBB:
                # received message data okay
                return Message(timestamp=timestamp, arbitration_id=arb_id,
                               dlc=dlc, data=data)
            else:
                return None

        else:
            return None

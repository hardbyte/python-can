#!/usr/bin/env python
# coding: utf-8

"""
A text based interface. For example use over serial ports like
"/dev/ttyS1" or "/dev/ttyUSB0" on Linux machines or "COM1" on Windows.
The interface is a simple implementation that has been used for
recording CAN traces.
"""

from __future__ import absolute_import, division

import logging
import struct

from can import BusABC, Message

logger = logging.getLogger('can.serial')

try:
    import serial
except ImportError:
    logger.warning("You won't be able to use the serial can backend without "
                   "the serial module installed!")
    serial = None


class SerialBus(BusABC):
    """
    Enable basic can communication over a serial device.

    .. note:: See :meth:`can.interfaces.serial.SerialBus._recv_internal`
              for some special semantics.

    """

    def __init__(self, channel, baudrate=115200, timeout=0.1, rtscts=False,
                 *args, **kwargs):
        """
        :param str channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.

        :param int baudrate:
            Baud rate of the serial device in bit/s (default 115200).

            .. warning::
                Some serial port implementations don't care about the baudrate.

        :param float timeout:
            Timeout for the serial device in seconds (default 0.1).

        :param bool rtscts:
            turn hardware handshake (RTS/CTS) on and off

        """
        if not channel:
            raise ValueError("Must specify a serial port.")

        self.channel_info = "Serial interface: " + channel
        self.ser = serial.serial_for_url(
            channel, baudrate=baudrate, timeout=timeout, rtscts=rtscts)

        super(SerialBus, self).__init__(channel=channel, *args, **kwargs)

    def shutdown(self):
        """
        Close the serial interface.
        """
        self.ser.close()

    def send(self, msg, timeout=None):
        """
        Send a message over the serial device.

        :param can.Message msg:
            Message to send.

            .. note:: Flags like ``extended_id``, ``is_remote_frame`` and
                      ``is_error_frame`` will be ignored.

            .. note:: If the timestamp is a float value it will be converted
                      to an integer.

        :param timeout:
            This parameter will be ignored. The timeout value of the channel is
            used instead.

        """
        try:
            timestamp = struct.pack('<I', int(msg.timestamp * 1000))
        except struct.error:
            raise ValueError('Timestamp is out of range')
        try:
            a_id = struct.pack('<I', msg.arbitration_id)
        except struct.error:
            raise ValueError('Arbitration Id is out of range')
        byte_msg = bytearray()
        byte_msg.append(0xAA)
        for i in range(0, 4):
            byte_msg.append(timestamp[i])
        byte_msg.append(msg.dlc)
        for i in range(0, 4):
            byte_msg.append(a_id[i])
        for i in range(0, msg.dlc):
            byte_msg.append(msg.data[i])
        byte_msg.append(0xBB)
        self.ser.write(byte_msg)

    def _recv_internal(self, timeout):
        """
        Read a message from the serial device.

        :param timeout:

            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.

        :returns:
            Received message and False (because not filtering as taken place).

            .. warning::
                Flags like extended_id, is_remote_frame and is_error_frame
                will not be set over this function, the flags in the return
                message are the default values.

        :rtype:
            can.Message, bool
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte = self.ser.read()
        except serial.SerialException:
            return None, False

        if rx_byte and ord(rx_byte) == 0xAA:
            s = bytearray(self.ser.read(4))
            timestamp = (struct.unpack('<I', s))[0]
            dlc = ord(self.ser.read())

            s = bytearray(self.ser.read(4))
            arb_id = (struct.unpack('<I', s))[0]

            data = self.ser.read(dlc)

            rxd_byte = ord(self.ser.read())
            if rxd_byte == 0xBB:
                # received message data okay
                msg = Message(timestamp=timestamp/1000,
                              arbitration_id=arb_id,
                              dlc=dlc,
                              data=data)
                return msg, False

        else:
            return None, False

    def fileno(self):
        if hasattr(self.ser, 'fileno'):
            return self.ser.fileno()
        # Return an invalid file descriptor on Windows
        return -1

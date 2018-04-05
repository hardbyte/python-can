# coding: utf-8

"""
Name:        simpleserial.py
Purpose:     A text based interface. For example use over serial ports like
             "/dev/ttyS1" or "/dev/ttyUSB0" on Linux machines or "COM1" on Windows.
             The interface is a simple implementation that has been used for
             recording CAN traces.

Copyright:   2012 - 2017 Brian Thorne
             2014 Sam Bristow
             2015 Andrew Beal
             2015 Robert Kaye
             2016 - 2017 Christian Sandberg
             2016 Giuseppe Corbelli
             2016 Kyle Altendorf
             2017 Eduard Bröcker
             2017 - 2018 Boris Wenzlaff
             2018 Felix Divo

This file is part of python-can <https://github.com/hardbyte/python-can/>.

python-can is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

python-can is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with python-can. If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import struct
import serial
import time

from can.bus import BusABC
from can import CanError
from can.message import Message

logger = logging.getLogger(__name__)


class SimpleSerialBus(BusABC):
    """
    Enable basic can communication over a serial device.
    """

    def __init__(self, channel, serial_baudrate=115200, timeout=0.1, **kwargs):
        """
        :param str channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.

        :param int serial_baudrate:
            Baud rate of underlying serial or usb device in bit/s (default 115200).

            .. note:: Some serial port implementations don't care about the baud
                      rate.

        :param float timeout:
            Timeout for the serial device in seconds (default 0.1). The
            timeout will be used for sending and receiving.
        """

        if not channel:
            raise ValueError("Must specify a serial port.")

        self.channel_info = "Simple serial interface on: " + channel
        self.serial_timeout = timeout
        # TODO catch serial exception
        self.ser = serial.Serial(port=channel, baudrate=serial_baudrate, timeout=self.serial_timeout,
                                 write_timeout=self.serial_timeout)
        super(SimpleSerialBus, self).__init__(channel, **kwargs)

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

            .. note:: Flags like extended_id, is_remote_frame and is_error_frame
                      will be ignored.

            .. note:: If the timestamp a float value it will be convert to an
                      integer.

        :param float timeout:
            Timeout for sending messages in seconds, if no timeout is set the default from the constructor will be used.

        :raises: CanError: Will be raised on timeout while sending.
        """

        try:
            timestamp = struct.pack('<I', self.__convert_to_integer_milliseconds(msg.timestamp))
        except Exception:
            raise ValueError('Timestamp is out of range')
        try:
            a_id = struct.pack('<I', msg.arbitration_id)
        except Exception:
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
        try:
            if timeout is not None:
                self.ser.write(byte_msg, timeout)
            else:
                self.ser.write(byte_msg)
        except serial.SerialTimeoutException:
            raise CanError("Timeout while sending")

    @staticmethod
    def __convert_to_integer_milliseconds(msg_timestamp):
        return int(msg_timestamp * 1000)

    @staticmethod
    def __remaining_time(start_time, timeout):
        """
        :param start_time:
            Start time in seconds.
        :param timeout:
            Timeout in seconds.
        :return: Time left for timeout or None for unlimited time.
        """

        if timeout is None:
            return None
        r = timeout - (time.time() - start_time)
        if r < 0:
            return 0
        return r

    def recv(self, timeout=-1):
        """
        Read a message from the serial device.

        :param timeout:
            Timeout for receiving a message in seconds. If the timeout parameter not set,
            the default value from the constructor will be used. With timeout = None it
            will block until a message is read.
        :returns:
            Received message.

            .. note:: Flags like extended_id, is_remote_frame and is_error_frame
              will not be set over this function, the flags in the return
              message are the default values.

        :rtype:
            can.Message
        """

        if timeout < 0:
            timeout = self.serial_timeout

        try:
            start = time.time()
            self.ser.timeout = timeout
            rx_byte = self.ser.read()
            if len(rx_byte) and ord(rx_byte) == 0xAA:
                r_time = self.__remaining_time(start, timeout)
                self.ser.timeout = r_time
                s = bytearray(self.ser.read(4))
                timestamp = (struct.unpack('<I', s))[0]
                r_time = self.__remaining_time(start, timeout)
                self.ser.timeout = r_time
                dlc = ord(self.ser.read())
                r_time = self.__remaining_time(start, timeout)
                self.ser.timeout = r_time
                s = bytearray(self.ser.read(4))
                arb_id = (struct.unpack('<I', s))[0]
                r_time = self.__remaining_time(start, timeout)
                self.ser.timeout = r_time
                data = self.ser.read(dlc)
                r_time = self.__remaining_time(start, timeout)
                self.ser.timeout = r_time
                rxd_byte = ord(self.ser.read())
                if rxd_byte == 0xBB:
                    # received message data okay
                    return Message(timestamp=timestamp / 1000, arbitration_id=arb_id, dlc=dlc, data=data)
        except serial.SerialTimeoutException:
            return None
        finally:
            self.ser.timeout = self.serial_timeout

# coding: utf-8

"""
Name:        serialcom
Purpose:     Basic serial communication.

Copyright:   2018 Boris Wenzlaff

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

logger = logging.getLogger(__name__)

try:
    import serial #TODO add package to requirements
except ImportError:
    logger.warning("You won't be able to use the serial can backend without the serial module installed!")
    serial = None


class SerialInterface:
    """
    Basic serial communication.
    """
    serial_timeout = None

    def __init__(self, port=None, baudrate=115200, timeout=0.1):
        """
        Initialize the serial port. Will open the port after the initialisation.
        Default configuration:
            bytesize=EIGHTBITS
            parity=PARITY_NONE
            stopbits=STOPBITS_ONE
            xonxoff=False
            rtscts=False
            dsrdtr=False
            inter_byte_timeout=None
        :param str port:
            The serial device to open. For example "/dev/ttyS1" or "/dev/ttyUSB0"
            on Linux or "COM3" on Windows systems (default None).
        :param int baudrate:
            Bit rate of the serial device in bit/s (default 115200).
        :param timeout:
            Timeout for the serial device in seconds (default 0.1). The
            timeout will be used for sending and receiving.
        :raise ValueError:
            From Serial. Will be raised when parameter are out of range, e.g.
            baud rate.
        :raise SerialException:
            From Serial. In case the device can not be found or can not be
            configured.
        """
        self.ser = serial.Serial(port=port, baudrate=baudrate,
                                 timeout=timeout, write_timeout=timeout)
        self.serial_timeout = timeout
        logger.info("Init serial interface [port={}, baud rate={}, timeout={}]".format(port, baudrate, timeout))

    def close_port(self):
        """
        From Serial. Close port immediately.
        """
        self.ser.close()

    def send_serial(self, msg: bytes, timeout=serial_timeout):
        """
        From Serial. Write the msg to the port. This should be of type
        bytes (or compatible such as bytearray or memoryview). Unicode
        strings must be encoded (e.g. 'hello'.encode('utf-8').
        :param bytes msg:
            Data to send.
        :param float timeout:
            Timeout for sending in seconds. If the timeout parameter is not set, the default
            value from the constructor will be used.
        :returns:
            Number of bytes written.
        :rtype:
            int
        """
        set_timeout = False
        if timeout != self.serial_timeout and not (timeout is None):
            self.ser.write_timeout = timeout
            set_timeout = True
        try:
            return self.ser.write(msg)
        finally:
            if set_timeout:
                self.ser.write_timeout = self.serial_timeout

    def recv_serial(self, size=1, timeout=serial_timeout):
        """
        From Serial. Read size bytes from the serial port. If a timeout is
        set it may return less characters as requested. With timeout = None it
        will block until the requested number of bytes is read.
        :param float timeout:
            Timeout for receiving bytes in seconds. If the timeout parameter not set,
            the default value from the constructor will be used.
        :param int size:
            Bytes to read.
        :returns:
            Bytes read from the port.
        :rtype:
            bytes
        """
        set_timeout = False
        if timeout != self.serial_timeout:
            self.ser.timeout = timeout
            set_timeout = True
        rx_byte = self.ser.read(size=size)
        if set_timeout:
            self.ser.timeout = self.serial_timeout
        return rx_byte

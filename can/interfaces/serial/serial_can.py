#!/usr/bin/env python
# coding: utf-8

"""
A text based interface. For example use over serial ports like
"/dev/ttyS1" or "/dev/ttyUSB0" on Linux machines or "COM1" on Windows.
The interface is a simple implementation that has been used for
recording CAN traces.
"""

import logging
import struct
import serial
import time

from can.bus import BusABC
from can.message import Message
from can.interfaces.serial.serialcom import SerialInterface

logger = logging.getLogger(__name__)


class SerialBus(BusABC):
    """
    Enable basic can communication over a serial device.
    """

    serial_timeout = None

    def __init__(self, channel, *args, **kwargs):
        """
        :param str channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.
        :param int baudrate:
            Baud rate of the serial device in bit/s (default 115200).

            .. note:: Some serial port implementations don't care about the baud
                      rate.

        :param float timeout:
            Timeout for the serial device in seconds (default 0.1). The
            timeout will be used for sending and receiving.
        """
        if channel == '':
            raise ValueError("Must specify a serial port.")
        else:
            self.channel_info = "Serial interface: " + channel
            baud_rate = kwargs.get('baudrate', 115200)
            self.serial_timeout = kwargs.get('timeout', 0.1)
            self.ser = SerialInterface(port=channel, baudrate=baud_rate, timeout=self.serial_timeout)
        super(SerialBus, self).__init__(*args, **kwargs)

    def shutdown(self):
        """
        Close the serial interface.
        """
        self.ser.close_port()

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
        """

        try:
            timestamp = struct.pack('<I', self.convert_to_integer_milliseconds(msg.timestamp))
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
        self.ser.send_serial(byte_msg, timeout)

    @staticmethod
    def convert_to_integer_milliseconds(msg_timestamp):
        return int(msg_timestamp * 1000)

    @staticmethod
    def remaining_time(start_time, timeout):
        """
        :param start_time:
            Start time in seconds.
        :param timeout:
            Timeout in seconds.
        :return: Time left for timeout or None for unlimited time.
        """
        if timeout is None:
            return None
        return timeout - (time.time() - start_time)

    def recv(self, timeout=serial_timeout):
        """
        Read a message from the serial device.

        #TODO implement timeout correctly
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
        start = time.time()
        rx_byte = self.ser.recv_serial(timeout=timeout)
        if len(rx_byte) and ord(rx_byte) == 0xAA:
            r_time = self.remaining_time(start, timeout)
            s = bytearray(self.ser.recv_serial(4, timeout=r_time))
            timestamp = (struct.unpack('<I', s))[0]
            r_time = self.remaining_time(start, timeout)
            dlc = ord(self.ser.recv_serial(timeout=r_time))
            r_time = self.remaining_time(start, timeout)
            s = bytearray(self.ser.recv_serial(4, timeout=r_time))
            arb_id = (struct.unpack('<I', s))[0]
            r_time = self.remaining_time(start, timeout)
            data = self.ser.recv_serial(dlc, timeout=r_time)
            r_time = self.remaining_time(start, timeout)
            rxd_byte = ord(self.ser.recv_serial(timeout=r_time))
            if rxd_byte == 0xBB:
                # received message data okay
                return Message(timestamp=timestamp / 1000, arbitration_id=arb_id, dlc=dlc, data=data)

        # queue = Queue()
        # action_read_msg = Process(target=self.read_message, args=(queue,))
        # action_read_msg.start()
        # action_read_msg.join(timeout)
        # action_read_msg.terminate()
        # msg = queue.get()
        # queue.close()

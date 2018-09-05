#!/usr/bin/env python
# coding: utf-8

"""
Interface for slcan compatible interfaces (win32/linux).

.. note::

    Linux users can use slcand or socketcan as well.

"""

from __future__ import absolute_import

import time
import logging

from can import BusABC, Message

logger = logging.getLogger(__name__)

try:
    import serial
except ImportError:
    logger.warning("You won't be able to use the slcan can backend without "
                   "the serial module installed!")
    serial = None


class slcanBus(BusABC):
    """
    slcan interface
    """

    # the supported bitrates and their commands
    _BITRATES = {
        10000:      'S0',
        20000:      'S1',
        50000:      'S2',
        100000:     'S3',
        125000:     'S4',
        250000:     'S5',
        500000:     'S6',
        750000:     'S7',
        1000000:    'S8',
        83300:      'S9'
    }

    _SLEEP_AFTER_SERIAL_OPEN = 2  # in seconds

    def __init__(self, channel, ttyBaudrate=115200, bitrate=None,
                 rtscts=False, **kwargs):
        """
        :param str channel:
            port of underlying serial or usb device (e.g. /dev/ttyUSB0, COM8, ...)
            Must not be empty.
        :param int ttyBaudrate:
            baudrate of underlying serial or usb device
        :param int bitrate:
            Bitrate in bit/s
        :param float poll_interval:
            Poll interval in seconds when reading messages
        :param bool rtscts:
            turn hardware handshake (RTS/CTS) on and off
        """

        if not channel:  # if None or empty
            raise TypeError("Must specify a serial port.")

        if '@' in channel:
            (channel, ttyBaudrate) = channel.split('@')

        self.serialPortOrig = serial.serial_for_url(
            channel, baudrate=ttyBaudrate, rtscts=rtscts)

        time.sleep(self._SLEEP_AFTER_SERIAL_OPEN)

        if bitrate is not None:
            self.close()
            if bitrate in self._BITRATES:
                self.write(self._BITRATES[bitrate])
            else:
                raise ValueError("Invalid bitrate, choose one of " + (', '.join(self._BITRATES)) + '.')

        self.open()

        super(slcanBus, self).__init__(channel, ttyBaudrate=115200,
                                       bitrate=None, rtscts=False, **kwargs)

    def write(self, string):
        if not string.endswith('\r'):
            string += '\r'
        self.serialPortOrig.write(string.encode())
        self.serialPortOrig.flush()

    def open(self):
        self.write('O')

    def close(self):
        self.write('C')

    def _recv_internal(self, timeout):
        if timeout != self.serialPortOrig.timeout:
            self.serialPortOrig.timeout = timeout

        canId = None
        remote = False
        extended = False
        frame = []

        readStr = self.serialPortOrig.read_until(b'\r')

        if not readStr:
            return None, False
        else:
            readStr = readStr.decode()
            if readStr[0] == 'T':
                # extended frame
                canId = int(readStr[1:9], 16)
                dlc = int(readStr[9])
                extended = True
                for i in range(0, dlc):
                    frame.append(int(readStr[10 + i * 2:12 + i * 2], 16))
            elif readStr[0] == 't':
                # normal frame
                canId = int(readStr[1:4], 16)
                dlc = int(readStr[4])
                for i in range(0, dlc):
                    frame.append(int(readStr[5 + i * 2:7 + i * 2], 16))
            elif readStr[0] == 'r':
                # remote frame
                canId = int(readStr[1:4], 16)
                remote = True
            elif readStr[0] == 'R':
                # remote extended frame
                canId = int(readStr[1:9], 16)
                extended = True
                remote = True

            if canId is not None:
                msg = Message(arbitration_id=canId,
                              extended_id=extended,
                              timestamp=time.time(),   # Better than nothing...
                              is_remote_frame=remote,
                              dlc=dlc,
                              data=frame)
                return msg, False
            else:
                return None, False

    def send(self, msg, timeout=0):
        if timeout != self.serialPortOrig.write_timeout:
            self.serialPortOrig.write_timeout = timeout

        if msg.is_remote_frame:
            if msg.is_extended_id:
                sendStr = "R%08X0" % (msg.arbitration_id)
            else:
                sendStr = "r%03X0" % (msg.arbitration_id)
        else:
            if msg.is_extended_id:
                sendStr = "T%08X%d" % (msg.arbitration_id, msg.dlc)
            else:
                sendStr = "t%03X%d" % (msg.arbitration_id, msg.dlc)

            for i in range(0, msg.dlc):
                sendStr += "%02X" % msg.data[i]
        self.write(sendStr)

    def shutdown(self):
        self.close()

    def fileno(self):
        if hasattr(self.serialPortOrig, 'fileno'):
            return self.serialPortOrig.fileno()
        # Return an invalid file descriptor on Windows
        return -1

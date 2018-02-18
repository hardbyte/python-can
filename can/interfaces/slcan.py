"""
Interface for slcan compatible interfaces (win32/linux).

Note Linux users can use slcand/socketcan as well.
"""

from __future__ import absolute_import

import io
import time
import logging

import serial

from can import BusABC, Message

logger = logging.getLogger(__name__)


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

    _SLEEP_AFTER_SERIAL_OPEN = 2 # in seconds

    def write(self, string):
        if not string.endswith('\r'):
            string += '\r'
        self.serialPort.write(string.decode())
        self.serialPort.flush()

    def open(self):
        self.write('O')

    def close(self):
        self.write('C')

    def __init__(self, channel, ttyBaudrate=115200, timeout=1, bitrate=None, **kwargs):
        """
        :param string channel:
            port of underlying serial or usb device (e.g. /dev/ttyUSB0, COM8, ...)
            Must not be empty.
        :param int ttyBaudrate:
            baudrate of underlying serial or usb device
        :param int bitrate:
            Bitrate in bits/s
        :param float poll_interval:
            Poll interval in seconds when reading messages
        :param float timeout:
            timeout in seconds when reading message
        """

        if not channel: # if None or empty
            raise TypeError("Must specify a serial port.")

        if '@' in channel:
            (channel, ttyBaudrate) = channel.split('@')

        self.serialPortOrig = serial.Serial(channel, baudrate=ttyBaudrate, timeout=timeout)
        self.serialPort = io.TextIOWrapper(io.BufferedRWPair(self.serialPortOrig, self.serialPortOrig, 1),
                                           newline='\r', line_buffering=True)

        time.sleep(self._SLEEP_AFTER_SERIAL_OPEN)

        if bitrate is not None:
            self.close()
            if bitrate in self._BITRATES:
                self.write(self._BITRATES[bitrate])
            else:
                raise ValueError("Invalid bitrate, choose one of " + (', '.join(self._BITRATES)) + '.')

        self.open()
        super(slcanBus, self).__init__(channel, **kwargs)

    def recv(self, timeout=None):
        if timeout is not None:
            self.serialPortOrig.timeout = timeout

        canId = None
        remote = False
        extended = False
        frame = []
        readStr = self.serialPort.readline()
        if not readStr:
            return None
        else:
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
                return Message(arbitration_id=canId,
                               extended_id=extended,
                               timestamp=time.time(),   # Better than nothing...
                               is_remote_frame=remote,
                               dlc=dlc,
                               data=frame)
            else:
                return None

    def send(self, msg, timeout=None):
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

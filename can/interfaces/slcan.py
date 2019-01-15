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

    LINE_TERMINATOR = b'\r'
    OK = b'\r'
    ERROR = b'\a'

    def __init__(self, channel, ttyBaudrate=115200, bitrate=None,
                 sleep_after_open=_SLEEP_AFTER_SERIAL_OPEN,
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
        :param float sleep_after_open:
            Time to wait in seconds after opening serial connection
        :param bool rtscts:
            turn hardware handshake (RTS/CTS) on and off
        """

        if not channel:  # if None or empty
            raise TypeError("Must specify a serial port.")

        if '@' in channel:
            (channel, ttyBaudrate) = channel.split('@')

        self.serialPortOrig = serial.serial_for_url(
            channel, baudrate=ttyBaudrate, rtscts=rtscts)

        self._buffer = bytearray()

        time.sleep(sleep_after_open)

        if bitrate is not None:
            self.close()
            self.read(None)
            if bitrate in self._BITRATES:
                self.write(self._BITRATES[bitrate])
                self.read(None)
            else:
                raise ValueError("Invalid bitrate, choose one of " + (', '.join(self._BITRATES)) + '.')

        self.open()
        self.read(None)

        super(slcanBus, self).__init__(channel, ttyBaudrate=115200,
                                       bitrate=None, rtscts=False, **kwargs)

    def write(self, string):
        self.serialPortOrig.write(string.encode() + self.LINE_TERMINATOR)
        self.serialPortOrig.flush()
    
    def read(self, timeout):
        if timeout != self.serialPortOrig.timeout:
            self.serialPortOrig.timeout = timeout

        while (self.OK not in self._buffer and self.ERROR not in self._buffer):
            byte = self.serialPortOrig.read(1)
            if byte:
                self._buffer += byte
            else:
                logger.debug("Read timed out!")
                return None

        string = self._buffer.decode()

        del self._buffer[:]

        return string
    
    def flush(self):
        while self.serialPortOrig.in_waiting:
            self.serialPortOrig.read(1)
    
    def open(self):
        self.write('O')

    def close(self):
        self.write('C')

    def _recv_internal(self, timeout):
        canId = None
        remote = False
        extended = False
        frame = []

        string = self.read(timeout)

        if not string:
            pass
        elif string[0] == 'T':
            # extended frame
            canId = int(string[1:9], 16)
            dlc = int(string[9])
            extended = True
            for i in range(0, dlc):
                frame.append(int(string[10 + i * 2:12 + i * 2], 16))
        elif string[0] == 't':
            # normal frame
            canId = int(string[1:4], 16)
            dlc = int(string[4])
            for i in range(0, dlc):
                frame.append(int(string[5 + i * 2:7 + i * 2], 16))
        elif string[0] == 'r':
            # remote frame
            canId = int(string[1:4], 16)
            dlc = int(string[4])
            remote = True
        elif string[0] == 'R':
            # remote extended frame
            canId = int(string[1:9], 16)
            dlc = int(string[9])
            extended = True
            remote = True

        if canId is not None:
            msg = Message(arbitration_id=canId,
                            is_extended_id=extended,
                            timestamp=time.time(),   # Better than nothing...
                            is_remote_frame=remote,
                            dlc=dlc,
                            data=frame)
            return msg, False
        return None, False

    def send(self, msg, timeout=None):
        if timeout != self.serialPortOrig.write_timeout:
            self.serialPortOrig.write_timeout = timeout

        if msg.is_remote_frame:
            if msg.is_extended_id:
                sendStr = "R%08X%d" % (msg.arbitration_id, msg.dlc)
            else:
                sendStr = "r%03X%d" % (msg.arbitration_id, msg.dlc)
        else:
            if msg.is_extended_id:
                sendStr = "T%08X%d" % (msg.arbitration_id, msg.dlc)
            else:
                sendStr = "t%03X%d" % (msg.arbitration_id, msg.dlc)

            sendStr += "".join(["%02X" % b for b in msg.data])
        self.write(sendStr)

    def shutdown(self):
        self.close()
        self.serialPortOrig.close()

    def fileno(self):
        if hasattr(self.serialPortOrig, 'fileno'):
            return self.serialPortOrig.fileno()
        # Return an invalid file descriptor on Windows
        return -1

    def get_version(self, timeout = None):
        cmd = "V"
        self.flush()
        self.write(cmd)
        string = self.read(timeout)
        
        if not string:
            pass
        elif string[0] == cmd and len(string) == 6:
            # convert ASCII coded version
            hw_version = int(string[1:3])
            sw_version = int(string[3:5])
            return hw_version, sw_version
        
        return None, None
    
    def get_serial(self, timeout = None):
        cmd = "N"
        self.flush()
        self.write(cmd)
        string = self.read(timeout)
        
        if not string:
            pass
        elif string[0] == cmd and len(string) == 6:
            serial = string[1:]
            return serial
        
        return None
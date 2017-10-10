"""
Interface for slcan compatible interfaces (win32/linux).
(Linux could use slcand/socketcan also).
"""
from __future__ import absolute_import

import serial
import io
import time
import logging

from can import CanError, BusABC, Message


logger = logging.getLogger(__name__)

class slcanBus(BusABC):
    """slcan interface"""

    def write(self, str):
        if not str.endswith("\r"):
            str += "\r"
        self.serialPort.write(str.decode())
        self.serialPort.flush()

    def open(self):
        self.write("O")

    def close(self):
        self.write("C")


    def __init__(self, channel, ttyBaudrate=115200, timeout=1, bitrate=None, poll_interval=0.01 , **kwargs):
        """
        :param string channel:
            port of underlying serial or usb device (e.g. /dev/ttyUSB0, COM8, ...)
        :param int ttyBaudrate:
            baudrate of underlying serial or usb device
        :param int bitrate:
            Bitrate in bits/s
        :param float poll_interval:
            Poll interval in seconds when reading messages
        :param float timeout
            timeout in seconds when reading message
        """


        if channel == '':
            raise TypeError("Must specify a serial port.")
        if '@' in channel:
            (channel, ttyBaudrate) = channel.split('@')

        self.poll_interval = poll_interval

        self.serialPortOrig = serial.Serial(channel, baudrate=ttyBaudrate, timeout=timeout)
        self.serialPort = io.TextIOWrapper(io.BufferedRWPair(self.serialPortOrig, self.serialPortOrig, 1),
                                               newline='\r', line_buffering=True)

        time.sleep(2)
        if bitrate is not None:
            self.close()
            if bitrate == 10000:
                self.write('S0')
            elif bitrate == 20000:
                self.write('S1')
            elif bitrate == 50000:
                self.write('S2')
            elif bitrate == 100000:
                self.write('S3')
            elif bitrate == 125000:
                self.write('S4')
            elif bitrate == 250000:
                self.write('S5')
            elif bitrate == 500000:
                self.write('S6')
            elif bitrate == 750000:
                self.write('S7')
            elif bitrate == 1000000:
                self.write('S8')
            elif bitrate == 83300:
                self.write('S9')
            else:
                raise ValueError("Invalid bitrate, choose one of 10000 20000 50000 100000 125000 250000 500000 750000 1000000 83300")

        self.open()
        super(slcanBus, self).__init__(channel, **kwargs)

    def recv(self, timeout=None):
        if timeout is not None:
            self.serialPortOrig.timeout = timeout

        canId = None
        remote = False
        frame = []
        str = self.serialPort.readline()
        if str is None or len(str) == 0:
            return None
        else:
            if str[0] == 'T':  # entended frame
                canId = int(str[1:9], 16)
                dlc = int(str[9])
                extended = True
                for i in range(0, dlc):
                    frame.append(int(str[10 + i * 2:12 + i * 2], 16))
            elif str[0] == 't':  # normal frame
                canId = int(str[1:4], 16)
                dlc = int(str[4])
                for i in range(0, dlc):
                    frame.append(int(str[5 + i * 2:7 + i * 2], 16))
                extended = False
            elif str[0] == 'r':  # remote frame
                canId = int(str[1:4], 16)
                remote = True
            elif str[0] == 'R':  # remote extended frame
                canId = int(str[1:9], 16)
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
        if bool(msg.is_remote_frame):
            if bool(msg.is_extended_id):
                sendStr = "R%08X0" % (msg.arbitration_id)
            else:
                sendStr = "r%03X0" % (msg.arbitration_id)
        else:
            if bool(msg.is_extended_id):
                sendStr = "T%08X%d" % (msg.arbitration_id, msg.dlc)
            else:
                sendStr = "t%03X%d" % (msg.arbitration_id, msg.dlc)

            for i in range(0, msg.dlc):
                sendStr += "%02X" % msg.data[i]
        self.write(sendStr)


    def shutdown(self):
        self.close()
# coding: utf-8

"""
To Support the Seeed USB-Can analyzer interface. The device will appear
as a serial port, for example "/dev/ttyS1" or "/dev/ttyUSB0" on Linux
machines or "COM1" on Windows.
https://www.seeedstudio.com/USB-CAN-Analyzer-p-2888.html
SKU 114991193
See protoocl:
https://copperhilltech.com/blog/usbcan-analyzer-usb-to-can-bus-serial-protocol-definition/

this file uses Crc8Darc checksums.
"""

from __future__ import absolute_import, division

import logging
import struct
import binascii
from time import sleep, time
from can import BusABC, Message

logger = logging.getLogger('can.CanAnalyzer')

try:
    import serial
except ImportError:
    logger.warning("You won't be able to use the serial can backend without "
                   "the serial module installed!")
    serial = None

try:
    from crccheck.crc import Crc8Darc
except ImportError:
    logger.warning("The interface requires the install option crccheck.")


class CanAnalyzer(BusABC):
    """
    Enable basic can communication over a serial device.

    .. note:: See :meth:`can.interfaces.serial.CanAnalyzer._recv_internal`
              for some special semantics.

    """
    BITRATE = {
               1000000: 0x01,
               800000: 0x02,
               500000: 0x03,
               400000: 0x04,
               250000: 0x05,
               200000: 0x06,
               125000: 0x07,
               100000: 0x08,
               50000: 0x09,
               20000: 0x0A,
               10000: 0x0B,
               5000: 0x0C
              }

    FRAMETYPE = {
                 "STD":0x01,
                 "EXT":0x02
                }

    OPERATIONMODE = {
                     "normal":0x00,
                     "loopback":0x01,
                     "silent":0x02,
                     "loopback_and_silent":0x03
                    }

    def __init__(self, channel, baudrate=2000000, timeout=0.1, rtscts=False,
                 frame_type='STD', operation_mode='normal', bit_rate=500000,
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
        self.bit_rate = bit_rate
        self.frame_type = frame_type
        self.op_mode = operation_mode
        self.filter_id = bytearray([0x00, 0x00, 0x00, 0x00])
        self.mask_id = bytearray([0x00, 0x00, 0x00, 0x00])
        if not channel:
            raise ValueError("Must specify a serial port.")

        self.channel_info = "Serial interface: " + channel
        self.ser = serial.Serial(
            channel, baudrate=baudrate, timeout=timeout, rtscts=rtscts)

        super(CanAnalyzer, self).__init__(channel=channel, *args, **kwargs)
        self.init_frame()

    def shutdown(self):
        """
        Close the serial interface.
        """
        self.ser.close()

    def init_frame(self, timeout=None):

        byte_msg = bytearray()
        byte_msg.append(0xAA)     # Frame Start Byte 1
        byte_msg.append(0x55)     # Frame Start Byte 2

        byte_msg.append(0x12)     # Initialization Message ID

        byte_msg.append(CanAnalyzer.BITRATE[self.bit_rate])  # CAN Baud Rate
        byte_msg.append(CanAnalyzer.FRAMETYPE[self.frame_type])

        byte_msg.extend(self.filter_id)

        byte_msg.extend(self.mask_id)

        byte_msg.append(CanAnalyzer.OPERATIONMODE[self.op_mode])

        byte_msg.append(0x01)

        for i in range(0, 4):
            byte_msg.append(0x00)

        crc = Crc8Darc.calc(byte_msg[2:])
#        crc_byte = struct.pack('B', crc)

        byte_msg.append(crc)

        logger.debug("init_frm:\t" + byte_msg.hex())
        self.ser.write(byte_msg)

    def flush_buffer(self):
        self.ser.flushInput()

    def status_frame(self, timeout=None):
        byte_msg = bytearray()
        byte_msg.append(0xAA)     # Frame Start Byte 1
        byte_msg.append(0x55)     # Frame Start Byte 2
        byte_msg.append(0x04)     # Status Message ID
        byte_msg.append(0x00)     # In response packet - Rx error count
        byte_msg.append(0x00)     # In response packet - Tx error count

        for i in range(0, 14):
            byte_msg.append(0x00)

        crc = Crc8Darc.calc(byte_msg[2:])
        crc_byte = struct.pack('B', crc)

        byte_msg.append(crc_byte)

        logger.debug("status_frm:\t" + byte_msg.hex())
        self.ser.write(byte_msg)

    def send(self, msg, timeout=None):
        """
        Send a message over the serial device.

        :param can.Message msg:
            Message to send.

        :param timeout:
            This parameter will be ignored. The timeout value of the channel is
            used instead.
        """

        byte_msg = bytearray()
        byte_msg.append(0xAA)

        m_type = 0xc0
        if msg.is_extended_id:
            m_type += 1 << 5

        if msg.is_remote_frame:
            m_type += 1 << 4

        m_type += msg.dlc
        byte_msg.append(m_type)

        if msg.is_extended_id:
            a_id = struct.pack('<I', msg.arbitration_id)
        else:
            a_id = struct.pack('<H', msg.arbitration_id)

        byte_msg.extend(a_id)
        byte_msg.extend(msg.data)
        byte_msg.append(0x55)

        logger.debug("Sending:\t" + byte_msg.hex())
        self.ser.write(byte_msg)

    def _recv_internal(self, timeout):
        """
        Read a message from the serial device.

        :param timeout:

            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.

        :returns:
            Received message and False (because not filtering as taken place).

        :rtype:
            can.Message, bool
        """
        try:
            # ser.read can return an empty string
            # or raise a SerialException
            rx_byte_1 = self.ser.read()

        except serial.SerialException:
            return None, False

        if rx_byte_1 and  ord(rx_byte_1) == 0xAA:
            rx_byte_2 = ord(self.ser.read())
            time_stamp = time()
            if rx_byte_2 == 0x55:
                rx_msg_type = self.ser.read()

            else:
                length = int(rx_byte_2 & 0x0F)
                is_extended = bool(rx_byte_2 & 0x20)
                is_remote = bool(rx_byte_2 & 0x10)
                if is_extended:
                    s_3_4_5_6 = bytearray(self.ser.read(4))
                    arb_id = (struct.unpack('<I', s_3_4_5_6))[0]

                else:
                    s_3_4 = bytearray(self.ser.read(2))
                    arb_id = (struct.unpack('<H', s_3_4))[0]

                data = bytearray(self.ser.read(length))
                end_packet = ord(self.ser.read())
                if end_packet == 0x55:
                    msg = Message(timestamp=time_stamp,
                                  arbitration_id=arb_id,
                                  is_extended_id=is_extended,
                                  is_remote_frame=is_remote,
                                  dlc=length,
                                  data=data)
                    logger.debug("recv message: " + str(msg))
                    return msg, False

                else:
                    return None, False

        return None, None

    def fileno(self):
        if hasattr(self.ser, 'fileno'):
            return self.ser.fileno()
        # Return an invalid file descriptor on Windows
        return -1

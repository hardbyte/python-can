"""
Interface for slcan compatible interfaces (win32/linux).

.. note::

    Linux users can use slcand or socketcan as well.

"""

import time
import logging

from can import BusABC, Message

logger = logging.getLogger(__name__)

try:
    import serial
except ImportError:
    logger.warning(
        "You won't be able to use the slcan can backend without "
        "the serial module installed!"
    )
    serial = None


class slcanBus(BusABC):
    """
    slcan interface
    """

    # the supported bitrates and their commands
    _BITRATES = {
        10000: "S0",
        20000: "S1",
        50000: "S2",
        100000: "S3",
        125000: "S4",
        250000: "S5",
        500000: "S6",
        750000: "S7",
        1000000: "S8",
        83300: "S9",
    }

    _SLEEP_AFTER_SERIAL_OPEN = 2  # in seconds

    _OK = b"\r"
    _ERROR = b"\a"

    LINE_TERMINATOR = b"\r"

    def __init__(
        self,
        channel,
        ttyBaudrate=115200,
        bitrate=None,
        btr=None,
        sleep_after_open=_SLEEP_AFTER_SERIAL_OPEN,
        rtscts=False,
        **kwargs
    ):
        """
        :raise ValueError: if both *bitrate* and *btr* are set

        :param str channel:
            port of underlying serial or usb device (e.g. /dev/ttyUSB0, COM8, ...)
            Must not be empty.
        :param int ttyBaudrate:
            baudrate of underlying serial or usb device
        :param int bitrate:
            Bitrate in bit/s
        :param str btr:
            BTR register value to set custom can speed
        :param float poll_interval:
            Poll interval in seconds when reading messages
        :param float sleep_after_open:
            Time to wait in seconds after opening serial connection
        :param bool rtscts:
            turn hardware handshake (RTS/CTS) on and off
        """

        if not channel:  # if None or empty
            raise TypeError("Must specify a serial port.")
        if "@" in channel:
            (channel, ttyBaudrate) = channel.split("@")
        self.serialPortOrig = serial.serial_for_url(
            channel, baudrate=ttyBaudrate, rtscts=rtscts
        )

        self._buffer = bytearray()

        time.sleep(sleep_after_open)

        if bitrate is not None and btr is not None:
            raise ValueError("Bitrate and btr mutually exclusive.")
        if bitrate is not None:
            self.set_bitrate(bitrate)
        if btr is not None:
            self.set_bitrate_reg(btr)
        self.open()

        super().__init__(
            channel, ttyBaudrate=115200, bitrate=None, rtscts=False, **kwargs
        )

    def set_bitrate(self, bitrate):
        """
        :raise ValueError: if both *bitrate* is not among the possible values

        :param int bitrate:
            Bitrate in bit/s
        """
        self.close()
        if bitrate in self._BITRATES:
            self._write(self._BITRATES[bitrate])
        else:
            raise ValueError(
                "Invalid bitrate, choose one of " + (", ".join(self._BITRATES)) + "."
            )
        self.open()

    def set_bitrate_reg(self, btr):
        """
        :param str btr:
            BTR register value to set custom can speed
        """
        self.close()
        self._write("s" + btr)
        self.open()

    def _write(self, string):
        self.serialPortOrig.write(string.encode() + self.LINE_TERMINATOR)
        self.serialPortOrig.flush()

    def _read(self, timeout):

        # first read what is already in receive buffer
        while self.serialPortOrig.in_waiting:
            self._buffer += self.serialPortOrig.read()
        # if we still don't have a complete message, do a blocking read
        start = time.time()
        time_left = timeout
        while not (ord(self._OK) in self._buffer or ord(self._ERROR) in self._buffer):
            self.serialPortOrig.timeout = time_left
            byte = self.serialPortOrig.read()
            if byte:
                self._buffer += byte
            # if timeout is None, try indefinitely
            if timeout is None:
                continue
            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time.time() - start)
                if time_left > 0:
                    continue
                else:
                    return None
        # return first message
        for i in range(len(self._buffer)):
            if self._buffer[i] == ord(self._OK) or self._buffer[i] == ord(self._ERROR):
                string = self._buffer[: i + 1].decode()
                del self._buffer[: i + 1]
                break
        return string

    def flush(self):
        del self._buffer[:]
        while self.serialPortOrig.in_waiting:
            self.serialPortOrig.read()

    def open(self):
        self._write("O")

    def close(self):
        self._write("C")

    def _recv_internal(self, timeout):

        canId = None
        remote = False
        extended = False
        frame = []

        string = self._read(timeout)

        if not string:
            pass
        elif string[0] == "T":
            # extended frame
            canId = int(string[1:9], 16)
            dlc = int(string[9])
            extended = True
            for i in range(0, dlc):
                frame.append(int(string[10 + i * 2 : 12 + i * 2], 16))
        elif string[0] == "t":
            # normal frame
            canId = int(string[1:4], 16)
            dlc = int(string[4])
            for i in range(0, dlc):
                frame.append(int(string[5 + i * 2 : 7 + i * 2], 16))
        elif string[0] == "r":
            # remote frame
            canId = int(string[1:4], 16)
            dlc = int(string[4])
            remote = True
        elif string[0] == "R":
            # remote extended frame
            canId = int(string[1:9], 16)
            dlc = int(string[9])
            extended = True
            remote = True
        if canId is not None:
            msg = Message(
                arbitration_id=canId,
                is_extended_id=extended,
                timestamp=time.time(),  # Better than nothing...
                is_remote_frame=remote,
                dlc=dlc,
                data=frame,
            )
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
        self._write(sendStr)

    def shutdown(self):
        self.close()
        self.serialPortOrig.close()

    def fileno(self):
        if hasattr(self.serialPortOrig, "fileno"):
            return self.serialPortOrig.fileno()
        # Return an invalid file descriptor on Windows
        return -1

    def get_version(self, timeout):
        """Get HW and SW version of the slcan interface.

        :type timeout: int or None
        :param timeout:
            seconds to wait for version or None to wait indefinitely

        :returns: tuple (hw_version, sw_version)
            WHERE
            int hw_version is the hardware version or None on timeout
            int sw_version is the software version or None on timeout
        """
        cmd = "V"
        self._write(cmd)

        start = time.time()
        time_left = timeout
        while True:
            string = self._read(time_left)

            if not string:
                pass
            elif string[0] == cmd and len(string) == 6:
                # convert ASCII coded version
                hw_version = int(string[1:3])
                sw_version = int(string[3:5])
                return hw_version, sw_version
            # if timeout is None, try indefinitely
            if timeout is None:
                continue
            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time.time() - start)
                if time_left > 0:
                    continue
                else:
                    return None, None

    def get_serial_number(self, timeout):
        """Get serial number of the slcan interface.

        :type timeout: int or None
        :param timeout:
            seconds to wait for serial number or None to wait indefinitely

        :rtype str or None
        :return:
            None on timeout or a str object.
        """
        cmd = "N"
        self._write(cmd)

        start = time.time()
        time_left = timeout
        while True:
            string = self._read(time_left)

            if not string:
                pass
            elif string[0] == cmd and len(string) == 6:
                serial_number = string[1:-1]
                return serial_number
            # if timeout is None, try indefinitely
            if timeout is None:
                continue
            # try next one only if there still is time, and with
            # reduced timeout
            else:
                time_left = timeout - (time.time() - start)
                if time_left > 0:
                    continue
                else:
                    return None

"""
Interface for slcan compatible interfaces (win32/linux).
"""

from typing import Any, Optional, Tuple

import io
import time
import logging

from can import BusABC, Message
from ..exceptions import (
    CanInterfaceNotImplementedError,
    CanInitializationError,
    CanOperationError,
    error_check,
)
from can import typechecking


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
        channel: typechecking.ChannelStr,
        ttyBaudrate: int = 115200,
        bitrate: Optional[int] = None,
        btr: Optional[str] = None,
        sleep_after_open: float = _SLEEP_AFTER_SERIAL_OPEN,
        rtscts: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        :param str channel:
            port of underlying serial or usb device (e.g. ``/dev/ttyUSB0``, ``COM8``, ...)
            Must not be empty. Can also end with ``@115200`` (or similarly) to specify the baudrate.
        :param int ttyBaudrate:
            baudrate of underlying serial or usb device (Ignored if set via the ``channel`` parameter)
        :param bitrate:
            Bitrate in bit/s
        :param btr:
            BTR register value to set custom can speed
        :param poll_interval:
            Poll interval in seconds when reading messages
        :param sleep_after_open:
            Time to wait in seconds after opening serial connection
        :param rtscts:
            turn hardware handshake (RTS/CTS) on and off

        :raise ValueError: if both ``bitrate`` and ``btr`` are set or the channel is invalid
        :raise CanInterfaceNotImplementedError: if the serial module is missing
        :raise CanInitializationError: if the underlying serial connection could not be established
        """
        if serial is None:
            raise CanInterfaceNotImplementedError("The serial module is not installed")

        if not channel:  # if None or empty
            raise ValueError("Must specify a serial port.")
        if "@" in channel:
            (channel, baudrate) = channel.split("@")
            ttyBaudrate = int(baudrate)

        with error_check(exception_type=CanInitializationError):
            self.serialPortOrig = serial.serial_for_url(
                channel, baudrate=ttyBaudrate, rtscts=rtscts
            )

        self._buffer = bytearray()

        time.sleep(sleep_after_open)

        with error_check(exception_type=CanInitializationError):
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

    def set_bitrate(self, bitrate: int) -> None:
        """
        :param bitrate:
            Bitrate in bit/s

        :raise ValueError: if ``bitrate`` is not among the possible values
        """
        if bitrate in self._BITRATES:
            bitrate_code = self._BITRATES[bitrate]
        else:
            bitrates = ", ".join(str(k) for k in self._BITRATES.keys())
            raise ValueError(f"Invalid bitrate, choose one of {bitrates}.")

        self.close()
        self._write(bitrate_code)
        self.open()

    def set_bitrate_reg(self, btr: str) -> None:
        """
        :param btr:
            BTR register value to set custom can speed
        """
        self.close()
        self._write("s" + btr)
        self.open()

    def _write(self, string: str) -> None:
        with error_check("Could not write to serial device"):
            self.serialPortOrig.write(string.encode() + self.LINE_TERMINATOR)
            self.serialPortOrig.flush()

    def _read(self, timeout: Optional[float]) -> Optional[str]:

        with error_check("Could not read from serial device"):
            # first read what is already in receive buffer
            while self.serialPortOrig.in_waiting:
                self._buffer += self.serialPortOrig.read()
            # if we still don't have a complete message, do a blocking read
            start = time.time()
            time_left = timeout
            while not (
                ord(self._OK) in self._buffer or ord(self._ERROR) in self._buffer
            ):
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

    def flush(self) -> None:
        del self._buffer[:]
        with error_check("Could not flush"):
            while self.serialPortOrig.in_waiting:
                self.serialPortOrig.read()

    def open(self) -> None:
        self._write("O")

    def close(self) -> None:
        self._write("C")

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:

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

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
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

    def shutdown(self) -> None:
        super().shutdown()
        self.close()
        with error_check("Could not close serial socket"):
            self.serialPortOrig.close()

    def fileno(self) -> int:
        try:
            return self.serialPortOrig.fileno()
        except io.UnsupportedOperation:
            raise NotImplementedError(
                "fileno is not implemented using current CAN bus on this platform"
            )
        except Exception as exception:
            raise CanOperationError("Cannot fetch fileno") from exception

    def get_version(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[int], Optional[int]]:
        """Get HW and SW version of the slcan interface.

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

    def get_serial_number(self, timeout: Optional[float]) -> Optional[str]:
        """Get serial number of the slcan interface.

        :param timeout:
            seconds to wait for serial number or :obj:`None` to wait indefinitely

        :return:
            :obj:`None` on timeout or a :class:`str` object.
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

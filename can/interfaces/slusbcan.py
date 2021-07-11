"""
Interface for slcan over usb (slusb) (win32/macos/linux).

"""

from typing import Any, Optional, Tuple
from can import typechecking

import struct
import time
import logging

import usb.core
import usb.util

from can import BusABC, Message

logger = logging.getLogger(__name__)


class slUSBcanBus(BusABC):
    """
    slcan interface
    """

    # the supported bitrates and their commands
    _BITRATES = {
        10000: b'S\x00',
        20000: b'S\x01',
        50000: b'S\x02',
        100000: b'S\x03',
        125000: b'S\x04',
        250000: b'S\x05',
        500000: b'S\x06',
        750000: b'S\x07',
        1000000: b'S\x08'
    }

    _OK = b"\r"
    _ERROR = b"\a"

    LINE_TERMINATOR = b"\r"

    def __init__(
        self,
        channel: typechecking.ChannelStr,
        bitrate: Optional[int] = None,
        btr: Optional[str] = None,
        sleep_after_open: float = 2,
        **kwargs: Any
    ) -> None:
        """
        :raise ValueError: if both *bitrate* and *btr* are set

        :param bitrate:
            Bitrate in bit/s
        :param btr:
            BTR register value to set custom can speed
        :param poll_interval:
            Poll interval in seconds when reading messages
        :param sleep_after_open:
            Time to wait in seconds after opening connection
        """

        self._buffer = bytearray()

        time.sleep(sleep_after_open)

        dev = usb.core.find(idProduct=0xc1b0)
        assert(dev is not None)
        dev.set_configuration()
        self.dev = dev

        if bitrate is not None and btr is not None:
            raise ValueError("Bitrate and btr mutually exclusive.")
        if bitrate is not None:
            self.set_bitrate(bitrate)
        if btr is not None:
            self.set_bitrate_reg(btr)

        #cfg = dev.get_active_configuration()
        #intf = cfg[(0,0)]

        self.open()

        super().__init__(channel, bitrate=None, **kwargs)

    def set_bitrate(self, bitrate: int) -> None:
        """
        :raise ValueError: if both *bitrate* is not among the possible values

        :param bitrate:
            Bitrate in bit/s
        """
        if bitrate in self._BITRATES:
            self.set_bitrate_reg(self._BITRATES[bitrate])
        else:
            raise ValueError(
                "Invalid bitrate, choose one of "
                + (", ".join(str(k) for k in self._BITRATES.keys()))
                + "."
            )

    def set_bitrate_reg(self, btr: bytes) -> None:
        """
        :param btr:
            BTR register value to set custom can speed
        """
        self.close()
        self._write(btr)
        self.open()

    def _write(self, payload: bytes, timeout: int=0) -> None:
        payload = payload + self.LINE_TERMINATOR
        self.dev.write(0x1,  payload)

    def _read(self, timeout: Optional[float]) -> Optional[str]:

        start = time.time()
        time_left = timeout
        while not (ord(self._OK) in self._buffer or ord(self._ERROR) in self._buffer):
            self._buffer.extend(self.dev.read(0x81, 64))
            if timeout:
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

    def open(self) -> None:
        self._write(b'O')

    def close(self) -> None:
        self._write(b'C')

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

        if msg.is_remote_frame:
            if msg.is_extended_id:
                header = ord('R')
            else:
                header = ord('r')
            payload = struct.pack('<BHB', header, msg.arbitration_id, msg.dlc)
        else:
            if msg.is_extended_id:
                header = ord('T')
            else:
                header = ord('t')
            payload = struct.pack('<BHB', header, msg.arbitration_id, msg.dlc) + \
                bytes(msg.data)
        print(msg.arbitration_id)
        print(payload)
        self._write(payload, timeout)

    def shutdown(self) -> None:
        self.close()
        usb.util.dispose_resources(self.dev)

    def fileno(self) -> int:
        raise NotImplementedError(
            "fileno is not implemented using current CAN bus on this platform"
        )

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
        cmd = b'V'
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
            seconds to wait for serial number or None to wait indefinitely

        :return:
            None on timeout or a str object.
        """
        cmd = b'N'
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
